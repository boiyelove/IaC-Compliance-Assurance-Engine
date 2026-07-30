terraform {
  required_version = ">= 1.8.0, < 2.0.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.14"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_storage_account" "example" {
  name                              = "stcomplianceexample"
  resource_group_name               = "rg-compliance-example"
  location                          = "westeurope"
  account_tier                      = "Standard"
  account_replication_type          = "LRS"
  public_network_access_enabled     = false
  shared_access_key_enabled         = false
  min_tls_version                   = "TLS1_2"
  infrastructure_encryption_enabled = true
}
