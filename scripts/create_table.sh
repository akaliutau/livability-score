if [[ $# -ne 3 ]]; then
  echo "usage: create_table.sh project_id table schema_file"
  exit 1
fi

bq mk --table --schema="$3" \
   --time_partitioning_field=day \
   --time_partitioning_expiration 31536000 \
   --require_partition_filter=True \
   --project_id="$1" \
   "$2"
