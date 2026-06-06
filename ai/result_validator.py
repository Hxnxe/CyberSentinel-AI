import json
from typing import Any

from utils.logger import get_logger


logger = get_logger("analyzer")


def _normalize_common_result(result: dict, source_type: str) -> dict | None:
    """规范化分析结果并校验关键字段"""
    try:
        if not result:
            logger.error("分析结果为空")
            return None

        required_fields: dict[str, type] = {
            "summary": str,
            "risk_level": str,
            "key_points": list,
            "technical_details": list,
            "affected_components": list,
            "is_valuable": bool,
            "value_reason": str,
        }

        if source_type == "cve":
            required_fields.update({"cve_id": str, "exploit_status": str})

        for field, field_type in required_fields.items():
            if field not in result:
                logger.error(f"分析结果缺少必需字段: {field}")
                return None
            if not isinstance(result[field], field_type):
                logger.error(
                    f"字段 {field} 的类型错误，期望 {field_type.__name__}，实际为 {type(result[field]).__name__}"
                )
                return None

        valid_risk_levels = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
        risk_level = result["risk_level"].upper()
        if risk_level not in valid_risk_levels:
            logger.error(f"无效的风险等级: {risk_level}，使用默认值 MEDIUM")
            risk_level = "MEDIUM"
        result["risk_level"] = risk_level

        if source_type == "repository" and "security_type" in result:
            valid_security_types = {
                "POC收集",
                "漏洞利用框架",
                "安全工具",
                "安全研究",
                "POC更新",
                "漏洞利用",
                "安全修复",
                "安全功能",
            }
            security_type = result["security_type"]
            if security_type not in valid_security_types:
                logger.warning(f"无效的安全类型: {security_type}，使用默认值 安全研究")
                security_type = "安全研究"
            result["security_type"] = security_type

        if source_type == "cve":
            valid_exploit_status = {"POC可用", "漏洞利用可用", "理论可行", "未知"}
            exploit_status = result["exploit_status"]
            if exploit_status not in valid_exploit_status:
                logger.warning(f"无效的利用状态: {exploit_status}，使用默认值 未知")
                exploit_status = "未知"
            result["exploit_status"] = exploit_status

        for field in ["key_points", "technical_details", "affected_components"]:
            if not result[field] or not any(item for item in result[field] if item and item != "Unknown"):
                logger.error(f"字段 {field} 为空或仅包含无效值")
                return None

        result["is_valuable"] = bool(result.get("is_valuable", False))
        if not result.get("value_reason"):
            result["value_reason"] = "未提供价值说明"

        if source_type == "repository":
            # watched/update 仓库不依赖 relevance_score 判定价值
            is_watched = result.get("is_watched", False)
            is_update = result.get("is_update", False)

            relevance_score = result.get("relevance_score", "LOW")
            if relevance_score not in ["HIGH", "MEDIUM", "LOW"]:
                relevance_score = "LOW"
            result["relevance_score"] = relevance_score

            if not is_watched and not is_update and relevance_score == "LOW":
                result["is_valuable"] = False
                result["value_reason"] = f"与搜索关键词 '{result.get('search_keyword', 'N/A')}' 相关性不足"
        return result
    except Exception as e:
        logger.error(f"验证分析结果时出错: {str(e)}")
        return None


def _process_repo_analysis_result(result: dict | str, repo_data: dict, processed_commits: list) -> dict | None:
    """清理并补齐仓库分析结果"""
    try:
        if not result:
            logger.error("分析结果为空")
            return None

        if isinstance(result, str):
            logger.info("解析JSON字符串结果")
            result = json.loads(result)

        cleaned_result: dict[str, Any] = {}
        for key, value in result.items():
            if value is None or value == "Unknown":
                continue
            if isinstance(value, list):
                cleaned_list = [item for item in value if item and item != "Unknown"]
                if cleaned_list:
                    cleaned_result[key] = cleaned_list
            else:
                cleaned_result[key] = value

        repo_name = repo_data.get("name", "unknown")
        if "/" in repo_name:
            repo_name = repo_name.split("/")[-1]

        if not cleaned_result.get("short_description"):
            description = str(repo_data.get("description", "")).strip()
            if description:
                short_desc = description[:20] + ("..." if len(description) > 20 else "")
            else:
                security_type = cleaned_result.get("security_type", "安全工具")
                if "POC" in security_type or "poc" in security_type.lower():
                    short_desc = "漏洞利用验证工具"
                elif "漏洞利用" in security_type:
                    short_desc = "漏洞利用框架"
                elif "安全工具" in security_type:
                    short_desc = "网络安全工具集"
                elif "安全研究" in security_type:
                    short_desc = "安全研究项目"
                else:
                    short_desc = "安全相关项目"
            cleaned_result["short_description"] = short_desc

        cleaned_result.update(
            {
                "repository_name": repo_name,
                "repository_url": repo_data.get("url"),
                "commits_analyzed": len(processed_commits),
                "files_changed": sum(len(commit.get("files", [])) for commit in processed_commits),
                "is_watched": repo_data.get("is_watched", False),
                "is_update": repo_data.get("is_update", False),
                "search_keyword": repo_data.get("search_keyword", "N/A"),
            }
        )

        if not cleaned_result.get("summary") and cleaned_result.get("one_line_summary"):
            cleaned_result["summary"] = cleaned_result["one_line_summary"]

        return cleaned_result
    except Exception as e:
        logger.error(f"处理分析结果时出错: {str(e)}")
        return None


def validate_cve_result(result: dict, cve_data: dict) -> dict | None:
    """验证并增强 CVE 分析结果"""
    if not result:
        return None

    result.update(
        {
            "cve_id": cve_data.get("cve_id"),
            "repository_url": cve_data.get("repository_url"),
            "published_date": cve_data.get("published_date"),
            "last_modified": cve_data.get("last_modified"),
            "stars": cve_data.get("stars", 0),
        }
    )

    normalized_result = _normalize_common_result(result, "cve")
    if not normalized_result:
        return None

    if not normalized_result.get("is_valuable", False):
        normalized_result["value_reason"] = "不满足推送条件"
        logger.info(f"CVE {normalized_result['cve_id']} 不满足推送条件")
    elif normalized_result["risk_level"] not in ["CRITICAL", "HIGH"]:
        normalized_result["is_valuable"] = False
        normalized_result["value_reason"] = f"风险等级较低 ({normalized_result['risk_level']})"
        logger.info(f"CVE {normalized_result['cve_id']} 风险等级较低")
    elif normalized_result["exploit_status"] == "未知":
        normalized_result["is_valuable"] = False
        normalized_result["value_reason"] = "利用状态未知"
        logger.info(f"CVE {normalized_result['cve_id']} 利用状态未知")
    elif not any(comp and comp != "Unknown" for comp in normalized_result["affected_components"]):
        normalized_result["is_valuable"] = False
        normalized_result["value_reason"] = "没有明确的受影响组件"
        logger.info(f"CVE {normalized_result['cve_id']} 没有明确的受影响组件")

    return normalized_result


def validate_repo_result(result: dict, repo_data: dict, processed_commits: list) -> dict | None:
    """验证并规范化仓库分析结果"""
    processed_result = _process_repo_analysis_result(result, repo_data, processed_commits)
    if not processed_result:
        return None
    return _normalize_common_result(processed_result, "repository")


def validate_article_result(result: dict) -> dict | None:
    """验证文章分类结果结构"""
    try:
        if not result or not isinstance(result, dict):
            return None

        articles = result.get("articles")
        if not isinstance(articles, list):
            return None

        valid_articles = []
        for article in articles:
            if not isinstance(article, dict):
                continue
            title = article.get("title")
            category = article.get("category")
            if isinstance(title, str) and isinstance(category, str) and title.strip() and category.strip():
                valid_articles.append({"title": title, "category": category})

        if not valid_articles:
            return None
        return {"articles": valid_articles}
    except Exception as e:
        logger.error(f"验证文章分类结果失败: {str(e)}")
        return None
