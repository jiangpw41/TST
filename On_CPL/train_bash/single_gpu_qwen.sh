cd /home/jiangpeiwen2/jiangpeiwen2/workspace/LLaMA-Factory
echo "Current directory is: $(pwd)"
source activate llama_factory

number=5

model_name_or_path="/home/jiangpeiwen2/jiangpeiwen2/workspace/LLMs/Qwen1.5-7B-Chat"
output_dir="/home/jiangpeiwen2/jiangpeiwen2/TKGT/test/CPL_dynamic/v1/models/ft_intermediate/$number"
export_dir="/home/jiangpeiwen2/jiangpeiwen2/TKGT/test/CPL_dynamic/v1/models/$number"

CUDA_VISIBLE_DEVICES=2 python src/train_bash.py \
    --stage sft \
    --do_train \
    --model_name_or_path $model_name_or_path \
    --dataset CPL_table_ft_list \
    --dataset_dir data \
    --template default \
    --finetuning_type lora \
    --lora_target all \
    --output_dir $output_dir \
    --overwrite_cache \
    --overwrite_output_dir \
    --cutoff_len 4096 \
    --preprocessing_num_workers 16 \
    --per_device_train_batch_size 1 \
    --per_device_eval_batch_size 1 \
    --gradient_accumulation_steps 4 \
    --lr_scheduler_type cosine \
    --logging_steps 50 \
    --warmup_steps 50 \
    --save_steps 50 \
    --eval_steps 50 \
    --evaluation_strategy steps \
    --load_best_model_at_end \
    --learning_rate 5e-5 \
    --num_train_epochs 4.0 \
    --load_best_model_at_end \
    --max_samples 50000 \
    --val_size 0.1 \
    --ddp_timeout 180000000 \
    --plot_loss \
    --fp16 \
    --resume_from_checkpoint /home/jiangpeiwen2/jiangpeiwen2/TKGT/test/CPL_dynamic/v1/models/ft_intermediate/5/checkpoint-2450 \


echo "微调完成，开始merge"

export CUDA_VISIBLE_DEVICES=6

python src/export_model.py \
    --model_name_or_path $model_name_or_path \
    --adapter_name_or_path $output_dir \
    --template default \
    --finetuning_type lora \
    --export_dir $export_dir \
    --export_size 2 \
    --export_device cpu \
    --export_legacy_format False \

cp "$model_name_or_path/tokenizer_config.json" "$export_dir/tokenizer_config.json"
echo "merge完成"