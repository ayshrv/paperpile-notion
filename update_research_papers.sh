eval "$(conda shell.bash hook)"
conda activate paperpile-notion
python $HOME/repos/paperpile-notion/update_notion_db.py \
    --input "$1" \
    --config $HOME/repos/paperpile-notion/config.yaml \
    --database $NOTION_PAPER_DATABASE \
    --token $NOTION_TOKEN_V2 