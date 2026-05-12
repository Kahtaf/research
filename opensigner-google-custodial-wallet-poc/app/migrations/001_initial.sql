CREATE TABLE IF NOT EXISTS users (
  id CHAR(36) PRIMARY KEY,
  google_sub VARCHAR(255) NOT NULL UNIQUE,
  google_email VARCHAR(320) NOT NULL,
  opensigner_user_uuid CHAR(36) NOT NULL UNIQUE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_login_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wallets (
  id CHAR(36) PRIMARY KEY,
  internal_user_id CHAR(36) NOT NULL,
  opensigner_user_uuid CHAR(36) NOT NULL,
  opensigner_account_uuid VARCHAR(128),
  wallet_address VARCHAR(128) NOT NULL,
  custody_model VARCHAR(32) NOT NULL,
  recovery_method VARCHAR(32) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_used_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_wallet_user (internal_user_id),
  KEY idx_wallet_opensigner_user (opensigner_user_uuid),
  CONSTRAINT fk_wallet_user FOREIGN KEY (internal_user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS signing_audit_logs (
  id CHAR(36) PRIMARY KEY,
  internal_user_id CHAR(36) NOT NULL,
  wallet_id CHAR(36) NOT NULL,
  wallet_address VARCHAR(128) NOT NULL,
  message_hash VARCHAR(128) NOT NULL,
  signature_hash VARCHAR(128) NOT NULL,
  verification_result BOOLEAN NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_signing_audit_user_time (internal_user_id, created_at),
  KEY idx_signing_audit_wallet_time (wallet_id, created_at)
);

CREATE TABLE IF NOT EXISTS hot_signers (
  id CHAR(36) PRIMARY KEY,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS hot_accounts (
  id CHAR(36) PRIMARY KEY,
  address VARCHAR(128) NOT NULL UNIQUE,
  opensigner_user_uuid CHAR(36) NOT NULL,
  chain_id BIGINT NOT NULL,
  auth_provider VARCHAR(64) NOT NULL,
  signer_id CHAR(36) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_hot_account_user_chain_provider (opensigner_user_uuid, chain_id, auth_provider),
  KEY idx_hot_account_signer (signer_id),
  CONSTRAINT fk_hot_account_signer FOREIGN KEY (signer_id) REFERENCES hot_signers(id)
);

CREATE TABLE IF NOT EXISTS hot_devices (
  id CHAR(36) PRIMARY KEY,
  encrypted_share TEXT NOT NULL,
  is_primary BOOLEAN NOT NULL DEFAULT FALSE,
  signer_id CHAR(36) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_hot_device_signer_primary (signer_id, is_primary),
  CONSTRAINT fk_hot_device_signer FOREIGN KEY (signer_id) REFERENCES hot_signers(id)
);
