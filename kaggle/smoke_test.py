import kaggle_benchmarks as kbench


@kbench.task(name="ves-smoke-test-2")
def ves_smoke_test(llm) -> bool:
    reply = llm.prompt("Reply with the single word: ready")
    return "ready" in reply.lower()


ves_smoke_test.run(kbench.llm)
