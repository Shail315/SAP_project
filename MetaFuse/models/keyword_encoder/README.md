---
tags:
- sentence-transformers
- sentence-similarity
- feature-extraction
- dense
- generated_from_trainer
- dataset_size:437029
- loss:MultipleNegativesRankingLoss
base_model: sentence-transformers/all-MiniLM-L6-v2
widget:
- source_sentence: Adam Dunn had the weirdest career in MLB history | Dorktown Sports
  sentences:
  - '"adam dunn strikeouts"'
  - '"rupaul"'
  - '"basic"'
- source_sentence: Types Of Phone Users You'll Meet | Hasley India Comedy
  sentences:
  - '"super bowl halftime show"'
  - '"jayamala congress rv deshpande"'
  - '"videos"'
- source_sentence: School Days - Boys vs Girls | Lalit Shokeen Films | Entertainment
  sentences:
  - '"serial"'
  - '"incubating eggs"'
  - '"hypstar"'
- source_sentence: Flop Actresses Of Bollywood Who Married For Money | You will Be
    Shocked by This Entertainment
  sentences:
  - '"1990s kids shows"'
  - '"incident"'
  - '"flop actress marry for money"'
- source_sentence: Elizabeth Olsen's Boyfriend Is Now Her Roommate Entertainment
  sentences:
  - '"hero nani"'
  - '"boy - charlie puth"'
  - '"joke"'
pipeline_tag: sentence-similarity
library_name: sentence-transformers
---

# SentenceTransformer based on sentence-transformers/all-MiniLM-L6-v2

This is a [sentence-transformers](https://www.SBERT.net) model finetuned from [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2). It maps sentences & paragraphs to a 384-dimensional dense vector space and can be used for semantic textual similarity, semantic search, paraphrase mining, text classification, clustering, and more.

## Model Details

### Model Description
- **Model Type:** Sentence Transformer
- **Base model:** [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) <!-- at revision c9745ed1d9f207416be6d2e6f8de32d1f16199bf -->
- **Maximum Sequence Length:** 256 tokens
- **Output Dimensionality:** 384 dimensions
- **Similarity Function:** Cosine Similarity
<!-- - **Training Dataset:** Unknown -->
<!-- - **Language:** Unknown -->
<!-- - **License:** Unknown -->

### Model Sources

- **Documentation:** [Sentence Transformers Documentation](https://sbert.net)
- **Repository:** [Sentence Transformers on GitHub](https://github.com/huggingface/sentence-transformers)
- **Hugging Face:** [Sentence Transformers on Hugging Face](https://huggingface.co/models?library=sentence-transformers)

### Full Model Architecture

```
SentenceTransformer(
  (0): Transformer({'max_seq_length': 256, 'do_lower_case': False, 'architecture': 'BertModel'})
  (1): Pooling({'word_embedding_dimension': 384, 'pooling_mode_cls_token': False, 'pooling_mode_mean_tokens': True, 'pooling_mode_max_tokens': False, 'pooling_mode_mean_sqrt_len_tokens': False, 'pooling_mode_weightedmean_tokens': False, 'pooling_mode_lasttoken': False, 'include_prompt': True})
  (2): Normalize()
)
```

## Usage

### Direct Usage (Sentence Transformers)

First install the Sentence Transformers library:

```bash
pip install -U sentence-transformers
```

Then you can load this model and run inference.
```python
from sentence_transformers import SentenceTransformer

# Download from the 🤗 Hub
model = SentenceTransformer("sentence_transformers_model_id")
# Run inference
sentences = [
    "Elizabeth Olsen's Boyfriend Is Now Her Roommate Entertainment",
    '"joke"',
    '"hero nani"',
]
embeddings = model.encode(sentences)
print(embeddings.shape)
# [3, 384]

# Get the similarity scores for the embeddings
similarities = model.similarity(embeddings, embeddings)
print(similarities)
# tensor([[ 1.0000,  0.5390, -0.0964],
#         [ 0.5390,  1.0000, -0.1602],
#         [-0.0964, -0.1602,  1.0000]])
```

<!--
### Direct Usage (Transformers)

<details><summary>Click to see the direct usage in Transformers</summary>

</details>
-->

<!--
### Downstream Usage (Sentence Transformers)

You can finetune this model on your own dataset.

<details><summary>Click to expand</summary>

</details>
-->

<!--
### Out-of-Scope Use

*List how the model may foreseeably be misused and address what users ought not to do with the model.*
-->

<!--
## Bias, Risks and Limitations

*What are the known or foreseeable issues stemming from this model? You could also flag here known failure cases or weaknesses of the model.*
-->

<!--
### Recommendations

*What are recommendations with respect to the foreseeable issues? For example, filtering explicit content.*
-->

## Training Details

### Training Dataset

#### Unnamed Dataset

* Size: 437,029 training samples
* Columns: <code>sentence_0</code> and <code>sentence_1</code>
* Approximate statistics based on the first 1000 samples:
  |         | sentence_0                                                                        | sentence_1                                                                       |
  |:--------|:----------------------------------------------------------------------------------|:---------------------------------------------------------------------------------|
  | type    | string                                                                            | string                                                                           |
  | details | <ul><li>min: 4 tokens</li><li>mean: 19.38 tokens</li><li>max: 69 tokens</li></ul> | <ul><li>min: 3 tokens</li><li>mean: 6.89 tokens</li><li>max: 17 tokens</li></ul> |
* Samples:
  | sentence_0                                                                                      | sentence_1                    |
  |:------------------------------------------------------------------------------------------------|:------------------------------|
  | <code>4 Cameron Ka Dhokha \| Honor 9 Lite unboxing \| Giveaway Science & Technology</code>      | <code>"unboxing"</code>       |
  | <code>Cardi B Acceptance Speech - Best New Artist \| 2018 iHeartRadio Music Awards Music</code> | <code>"cardi b awards"</code> |
  | <code>Ellen Is in Justin Bieber’s 'Mistletoe' Entertainment</code>                              | <code>"holiday"</code>        |
* Loss: [<code>MultipleNegativesRankingLoss</code>](https://sbert.net/docs/package_reference/sentence_transformer/losses.html#multiplenegativesrankingloss) with these parameters:
  ```json
  {
      "scale": 20.0,
      "similarity_fct": "cos_sim",
      "gather_across_devices": false
  }
  ```

### Training Hyperparameters
#### Non-Default Hyperparameters

- `per_device_train_batch_size`: 32
- `per_device_eval_batch_size`: 32
- `num_train_epochs`: 2
- `multi_dataset_batch_sampler`: round_robin

#### All Hyperparameters
<details><summary>Click to expand</summary>

- `overwrite_output_dir`: False
- `do_predict`: False
- `eval_strategy`: no
- `prediction_loss_only`: True
- `per_device_train_batch_size`: 32
- `per_device_eval_batch_size`: 32
- `per_gpu_train_batch_size`: None
- `per_gpu_eval_batch_size`: None
- `gradient_accumulation_steps`: 1
- `eval_accumulation_steps`: None
- `torch_empty_cache_steps`: None
- `learning_rate`: 5e-05
- `weight_decay`: 0.0
- `adam_beta1`: 0.9
- `adam_beta2`: 0.999
- `adam_epsilon`: 1e-08
- `max_grad_norm`: 1
- `num_train_epochs`: 2
- `max_steps`: -1
- `lr_scheduler_type`: linear
- `lr_scheduler_kwargs`: None
- `warmup_ratio`: 0.0
- `warmup_steps`: 0
- `log_level`: passive
- `log_level_replica`: warning
- `log_on_each_node`: True
- `logging_nan_inf_filter`: True
- `save_safetensors`: True
- `save_on_each_node`: False
- `save_only_model`: False
- `restore_callback_states_from_checkpoint`: False
- `no_cuda`: False
- `use_cpu`: False
- `use_mps_device`: False
- `seed`: 42
- `data_seed`: None
- `jit_mode_eval`: False
- `bf16`: False
- `fp16`: False
- `fp16_opt_level`: O1
- `half_precision_backend`: auto
- `bf16_full_eval`: False
- `fp16_full_eval`: False
- `tf32`: None
- `local_rank`: 0
- `ddp_backend`: None
- `tpu_num_cores`: None
- `tpu_metrics_debug`: False
- `debug`: []
- `dataloader_drop_last`: False
- `dataloader_num_workers`: 0
- `dataloader_prefetch_factor`: None
- `past_index`: -1
- `disable_tqdm`: False
- `remove_unused_columns`: True
- `label_names`: None
- `load_best_model_at_end`: False
- `ignore_data_skip`: False
- `fsdp`: []
- `fsdp_min_num_params`: 0
- `fsdp_config`: {'min_num_params': 0, 'xla': False, 'xla_fsdp_v2': False, 'xla_fsdp_grad_ckpt': False}
- `fsdp_transformer_layer_cls_to_wrap`: None
- `accelerator_config`: {'split_batches': False, 'dispatch_batches': None, 'even_batches': True, 'use_seedable_sampler': True, 'non_blocking': False, 'gradient_accumulation_kwargs': None}
- `parallelism_config`: None
- `deepspeed`: None
- `label_smoothing_factor`: 0.0
- `optim`: adamw_torch_fused
- `optim_args`: None
- `adafactor`: False
- `group_by_length`: False
- `length_column_name`: length
- `project`: huggingface
- `trackio_space_id`: trackio
- `ddp_find_unused_parameters`: None
- `ddp_bucket_cap_mb`: None
- `ddp_broadcast_buffers`: False
- `dataloader_pin_memory`: True
- `dataloader_persistent_workers`: False
- `skip_memory_metrics`: True
- `use_legacy_prediction_loop`: False
- `push_to_hub`: False
- `resume_from_checkpoint`: None
- `hub_model_id`: None
- `hub_strategy`: every_save
- `hub_private_repo`: None
- `hub_always_push`: False
- `hub_revision`: None
- `gradient_checkpointing`: False
- `gradient_checkpointing_kwargs`: None
- `include_inputs_for_metrics`: False
- `include_for_metrics`: []
- `eval_do_concat_batches`: True
- `fp16_backend`: auto
- `push_to_hub_model_id`: None
- `push_to_hub_organization`: None
- `mp_parameters`: 
- `auto_find_batch_size`: False
- `full_determinism`: False
- `torchdynamo`: None
- `ray_scope`: last
- `ddp_timeout`: 1800
- `torch_compile`: False
- `torch_compile_backend`: None
- `torch_compile_mode`: None
- `include_tokens_per_second`: False
- `include_num_input_tokens_seen`: no
- `neftune_noise_alpha`: None
- `optim_target_modules`: None
- `batch_eval_metrics`: False
- `eval_on_start`: False
- `use_liger_kernel`: False
- `liger_kernel_config`: None
- `eval_use_gather_object`: False
- `average_tokens_across_devices`: True
- `prompts`: None
- `batch_sampler`: batch_sampler
- `multi_dataset_batch_sampler`: round_robin
- `router_mapping`: {}
- `learning_rate_mapping`: {}

</details>

### Training Logs
| Epoch  | Step  | Training Loss |
|:------:|:-----:|:-------------:|
| 0.0366 | 500   | 1.9952        |
| 0.0732 | 1000  | 1.7081        |
| 0.1098 | 1500  | 1.5554        |
| 0.1464 | 2000  | 1.4414        |
| 0.1830 | 2500  | 1.311         |
| 0.2197 | 3000  | 1.2522        |
| 0.2563 | 3500  | 1.2032        |
| 0.2929 | 4000  | 1.1076        |
| 0.3295 | 4500  | 1.0662        |
| 0.3661 | 5000  | 1.0259        |
| 0.4027 | 5500  | 0.9616        |
| 0.4393 | 6000  | 0.9438        |
| 0.4759 | 6500  | 0.9199        |
| 0.5125 | 7000  | 0.8883        |
| 0.5491 | 7500  | 0.861         |
| 0.5857 | 8000  | 0.8423        |
| 0.6223 | 8500  | 0.8005        |
| 0.6590 | 9000  | 0.7959        |
| 0.6956 | 9500  | 0.7507        |
| 0.7322 | 10000 | 0.7466        |
| 0.7688 | 10500 | 0.7475        |
| 0.8054 | 11000 | 0.7123        |
| 0.8420 | 11500 | 0.6959        |
| 0.8786 | 12000 | 0.6865        |
| 0.9152 | 12500 | 0.6813        |
| 0.9518 | 13000 | 0.6391        |
| 0.9884 | 13500 | 0.6308        |
| 1.0250 | 14000 | 0.6077        |
| 1.0616 | 14500 | 0.5632        |
| 1.0983 | 15000 | 0.5582        |
| 1.1349 | 15500 | 0.57          |
| 1.1715 | 16000 | 0.5472        |
| 1.2081 | 16500 | 0.5495        |
| 1.2447 | 17000 | 0.5384        |
| 1.2813 | 17500 | 0.5189        |
| 1.3179 | 18000 | 0.5149        |
| 1.3545 | 18500 | 0.5351        |
| 1.3911 | 19000 | 0.5292        |
| 1.4277 | 19500 | 0.5138        |
| 1.4643 | 20000 | 0.493         |
| 1.5010 | 20500 | 0.4891        |
| 1.5376 | 21000 | 0.4937        |
| 1.5742 | 21500 | 0.4882        |
| 1.6108 | 22000 | 0.4915        |
| 1.6474 | 22500 | 0.4872        |
| 1.6840 | 23000 | 0.4828        |
| 1.7206 | 23500 | 0.466         |
| 1.7572 | 24000 | 0.4812        |
| 1.7938 | 24500 | 0.4776        |
| 1.8304 | 25000 | 0.4713        |
| 1.8670 | 25500 | 0.4727        |
| 1.9036 | 26000 | 0.4622        |
| 1.9403 | 26500 | 0.4737        |
| 1.9769 | 27000 | 0.4859        |


### Framework Versions
- Python: 3.12.12
- Sentence Transformers: 5.2.0
- Transformers: 4.57.6
- PyTorch: 2.9.0+cu126
- Accelerate: 1.12.0
- Datasets: 4.0.0
- Tokenizers: 0.22.2

## Citation

### BibTeX

#### Sentence Transformers
```bibtex
@inproceedings{reimers-2019-sentence-bert,
    title = "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks",
    author = "Reimers, Nils and Gurevych, Iryna",
    booktitle = "Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing",
    month = "11",
    year = "2019",
    publisher = "Association for Computational Linguistics",
    url = "https://arxiv.org/abs/1908.10084",
}
```

#### MultipleNegativesRankingLoss
```bibtex
@misc{henderson2017efficient,
    title={Efficient Natural Language Response Suggestion for Smart Reply},
    author={Matthew Henderson and Rami Al-Rfou and Brian Strope and Yun-hsuan Sung and Laszlo Lukacs and Ruiqi Guo and Sanjiv Kumar and Balint Miklos and Ray Kurzweil},
    year={2017},
    eprint={1705.00652},
    archivePrefix={arXiv},
    primaryClass={cs.CL}
}
```

<!--
## Glossary

*Clearly define terms in order to be accessible across audiences.*
-->

<!--
## Model Card Authors

*Lists the people who create the model card, providing recognition and accountability for the detailed work that goes into its construction.*
-->

<!--
## Model Card Contact

*Provides a way for people who have updates to the Model Card, suggestions, or questions, to contact the Model Card authors.*
-->