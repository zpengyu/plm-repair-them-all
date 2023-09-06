from concurrent.futures import ThreadPoolExecutor, as_completed
from elleelleaime.core.utils.jsonl import stream_jsonl, write_jsonl
from elleelleaime.generate.strategies.registry import PatchGenerationStrategyRegistry

from typing import List
import fire
import sys
import tqdm
import logging


def generate_candidate(chunk: List[dict], model_name: str, **kwargs) -> List[dict]:
    """
    Generates the candidate patch for the given sample and model.
    """

    generation_strategy = PatchGenerationStrategyRegistry.get_generation(
        model_name, **kwargs
    )

    for sample in tqdm.tqdm(
        chunk, "Generating candidates for a chunk", total=len(chunk)
    ):
        generation = generation_strategy.generate(sample["prompt"])
        sample["generation"] = generation

    return chunk


def entry_point(
    samples_path: str,
    model_name: str,
    n_workers: int = 4,
    **kwargs,
):
    """
    Generates the candidate patches given the samples and the model,
    and writes the results to f"candidates_{benchmark}_{prompt_strategy}_{model_name}.jsonl.gz"
    """
    results = []

    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = []

        samples = list(stream_jsonl(samples_path))
        chunks = [samples[i::n_workers] for i in range(n_workers)]

        for chunk in tqdm.tqdm(chunks, desc="Launching workers", total=len(chunks)):
            futures.append(
                executor.submit(generate_candidate, chunk, model_name, **kwargs)
            )

        logging.info("Generating candidates...")
        for future in tqdm.tqdm(
            as_completed(futures),
            desc="Waiting for chunks to be processed",
            total=len(futures),
        ):
            results.extend(future.result())

    # Write results to jsonl file
    benchmark = samples_path.split("_")[1]
    prompt_strategy = samples_path.split("_")[2].split(".")[0]
    kwargs_str = "_".join([f"{k}={v}" for k, v in kwargs.items()])
    write_jsonl(
        f"candidates_{benchmark}_{prompt_strategy}_{model_name}_{kwargs_str}.jsonl.gz",
        results,
    )


def main():
    logging.getLogger().setLevel(logging.INFO)
    fire.Fire(entry_point)


if __name__ == "__main__":
    sys.exit(main())