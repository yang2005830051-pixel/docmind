"""一键运行 DocMind 评估。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from eval.evaluate import load_dataset, evaluate_retrieval, evaluate_generation, print_report


def main():
    print("正在加载评估数据集...")
    dataset = load_dataset()
    print(f"已加载 {len(dataset)} 条评估用例")

    print("\n正在初始化检索器...")
    from src.retriever import Retriever
    retriever = Retriever()

    print("正在评估检索质量...")
    retrieval_result = evaluate_retrieval(retriever, dataset)

    # 生成质量评估需要完整的 RAG 链（需要 API Key）
    generation_result = None
    try:
        from config import DEEPSEEK_API_KEY, OPENAI_API_KEY
        if DEEPSEEK_API_KEY or OPENAI_API_KEY:
            print("正在评估生成质量...")
            from src.rag_chain import RAGChain
            rag = RAGChain(session_id="eval_session")
            generation_result = evaluate_generation(rag, dataset)
        else:
            print("跳过生成质量评估（未配置 API Key）")
    except Exception as e:
        print(f"生成质量评估失败: {e}")

    print_report(retrieval_result, generation_result)

    # 保存结果到文件
    import json
    output = {"retrieval": retrieval_result}
    if generation_result:
        output["generation"] = generation_result
    output_path = Path(__file__).parent / "results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到 {output_path}")


if __name__ == "__main__":
    main()
