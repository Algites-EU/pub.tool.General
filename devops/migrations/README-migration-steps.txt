R22 migration quick commands:
  bash devops/migrations/migrate_codegen_to_old.sh --dry-run
  bash devops/migrations/migrate_codegen_to_old.sh --apply
  git diff --find-renames --stat

No new canonical model is implemented here. See README-codegen-old.md.
