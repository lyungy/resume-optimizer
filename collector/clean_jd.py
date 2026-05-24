"""
JD 文本清洗 - 去除平台水印噪音
"""
import re
import sqlite3
from pathlib import Path


# 默认数据库路径（相对于项目根目录）
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "db" / "resume_optimizer.db"


def clean_jd_text(text: str) -> str:
    """
    清洗 JD 文本，去除 Boss直聘平台水印噪音
    """
    if not text:
        return text

    # 1. 去除各种形式的平台水印（优先长匹配）
    noise_patterns = [
        r'来自BOSS直聘',
        r'来自boss直聘',
        r'岗位[来自]*BOSS直聘',
        r'岗位[来自]*boss直聘',
        r'BOSS直聘',
        r'boss直聘',
        r'Boss直聘',
        r'boss',
        r'BOSS',
        r'Boss',
        r'kanzhun',
        r'直聘',
    ]

    cleaned = text
    for pattern in noise_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

    # 2. 清理因去除水印导致的多余空格
    cleaned = re.sub(r'  +', ' ', cleaned)

    # 3. 清理开头结尾空白
    cleaned = cleaned.strip()

    return cleaned


def clean_database(db_path: str = None):
    """清洗数据库中所有 JD 的 raw_text"""
    db = Path(db_path) if db_path else DEFAULT_DB_PATH
    if not db.exists():
        print(f"❌ 数据库不存在: {db}")
        return

    conn = sqlite3.connect(str(db))
    cursor = conn.cursor()

    # 获取所有 JD
    cursor.execute("SELECT id, title, raw_text FROM job_descriptions WHERE raw_text IS NOT NULL")
    rows = cursor.fetchall()

    print(f"共 {len(rows)} 条 JD 需要检查")

    cleaned_count = 0
    for jd_id, title, raw_text in rows:
        cleaned = clean_jd_text(raw_text)
        if cleaned != raw_text:
            cursor.execute(
                "UPDATE job_descriptions SET raw_text = ? WHERE id = ?",
                (cleaned, jd_id)
            )
            cleaned_count += 1
            removed_chars = len(raw_text) - len(cleaned)
            print(f"  ✅ 清洗: {title[:25]:<25} | 去除 {removed_chars} 字符")

    conn.commit()
    conn.close()

    print(f"\n完成: {cleaned_count}/{len(rows)} 条已清洗")


if __name__ == "__main__":
    clean_database()
