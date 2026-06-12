locals {
  env    = terraform.workspace
  prefix = "panpan-${local.env}"
}
