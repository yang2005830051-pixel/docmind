"""DocMind 评估系统 — 测量检索质量和回答质量。"""

import json
import sys
import time
from pathlib import Path
from typing import List, Dict

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_dataset(path: str = None) -> List[Dict]:
    """加载评估数据集。"""
    if path is None:
        path = Path(__file__).parent / "dataset.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_retrieval(retriever, dataset: List[Dict], top_k: int = 5) -> Dict:
    """评估检索质量：Recall@K 和 MRR。

    通过检查检索结果中是否包含预期关键词来评估。
    """
    total_recall = 0.0
    total_mrr = 0.0
    results = []

    for item in dataset:
        query = item["question"]
        expected = set(item.get("expected_keywords", []))

        try:
            retrieved = retriever.retrieve(query, top_k=top_k)
        except Exception as e:
            results.append({"id": item["id"], "query": query, "error": str(e)})
            continue

        # 将检索结果拼接成文本
        retrieved_text = " ".join([r["content"] for r in retrieved]).lower()

        # 计算命中数
        hits = sum(1 for kw in expected if kw.lower() in retrieved_text)
        recall = hits / len(expected) if expected else 0
        total_recall += recall

        # 计算 MRR（第一个命中的排名倒数）
        mrr = 0
        for rank, r in enumerate(retrieved, 1):
            content_lower = r["content"].lower()
            if any(kw.lower() in content_lower for kw in expected):
                mrr = 1.0 / rank
                break
        total_mrr += mrr

        results.append({
            "id": item["id"],
            "query": query,
            "recall": round(recall, 3),
            "mrr": round(mrr, 3),
            "retrieved_count": len(retrieved),
            "keywords_hit": hits,
            "keywords_total": len(expected),
        })

    n = len(dataset)
    return {
        "metrics": {
            "recall@k": round(total_recall / n, 4) if n else 0,
            "mrr": round(total_mrr / n, 4) if n else 0,
            "total_queries": n,
            "successful_queries": sum(1 for r in results if "error" not in r),
        },
        "details": results,
    }


def evaluate_generation(rag_chain, dataset: List[Dict]) -> Dict:
    """评估生成质量：关键词覆盖率和响应时间。

    简单但实用的评估方式：检查回答是否包含预期关键词。
    """
    total_coverage = 0.0
    total_time = 0.0
    results = []

    for item in dataset:
        query = item["question"]
        expected = set(item.get("expected_keywords", []))

        try:
            start = time.time()
            response_parts = []
            for chunk in rag_chain.query_stream(query):
                response_parts.append(chunk)
            elapsed = time.time() - start
            response = "".join(response_parts)
        except Exception as e:
            results.append({"id": item["id"], "query": query, "error": str(e)})
            continue

        response_lower = response.lower()
        hits = sum(1 for kw in expected if kw.lower() in response_lower)
        coverage = hits / len(expected) if expected else 0
        total_coverage += coverage
        total_time += elapsed

        results.append({
            "id": item["id"],
            "query": query,
            "coverage": round(coverage, 3),
            "response_time": round(elapsed, 2),
            "response_length": len(response),
            "keywords_hit": hits,
            "keywords_total": len(expected),
        })

    n = len([r for r in results if "error" not in r])
    return {
        "metrics": {
            "keyword_coverage": round(total_coverage / n, 4) if n else 0,
            "avg_response_time": round(total_time / n, 2) if n else 0,
            "total_queries": len(dataset),
            "successful_queries": n,
        },
        "details": results,
    }


def print_report(retrieval_result: Dict, generation_result: Dict = None):
    """打印评估报告。"""
    print("\n" + "=" * 60)
    print("  DocMind 评估报告")
    print("=" * 60)

    print("\n--- 检索质量 ---")
    m = retrieval_result["metrics"]
    print(f"  Recall@K:     {m['recall@k']:.4f}")
    print(f"  MRR:          {m['mrr']:.4f}")
    print(f"  成功查询:     {m['successful_queries']}/{m['total_queries']}")

    if generation_result:
        print("\n--- 生成质量 ---")
        m = generation_result["metrics"]
        print(f"  关键词覆盖率: {m['keyword_coverage']:.4f}")
        print(f"  平均响应时间: {m['avg_response_time']:.2f}s")
        print(f"  成功查询:     {m['successful_queries']}/{m['total_queries']}")

    print("\n--- 详细结果 ---")
    for r in retrieval_result["details"]:
        status = "ERROR" if "error" in r else f"R={r['recall']:.2f} M={r['mrr']:.2f}"
        print(f"  [{r['id']:2d}] {status}  {r['query'][:40]}")

    print("\n" + "=" * 60)
