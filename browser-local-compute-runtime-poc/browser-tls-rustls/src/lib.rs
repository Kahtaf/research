use std::io::{Cursor, ErrorKind, Read, Write};
use std::sync::Arc;

use js_sys::{Object, Reflect, Uint8Array};
use rustls::pki_types::{CertificateDer, PrivateKeyDer};
use rustls::{ServerConfig, ServerConnection};
use rustls_rustcrypto::provider;
use wasm_bindgen::prelude::*;

#[wasm_bindgen]
pub struct TlsServer {
    conn: ServerConnection,
}

#[wasm_bindgen]
impl TlsServer {
    #[wasm_bindgen(constructor)]
    pub fn new(cert_pem: &str, key_pem: &str) -> Result<TlsServer, JsValue> {
        let certs = parse_certs(cert_pem)?;
        let key = parse_private_key(key_pem)?;
        let mut config = ServerConfig::builder_with_provider(Arc::new(provider()))
            .with_safe_default_protocol_versions()
            .map_err(to_js_error)?
            .with_no_client_auth()
            .with_single_cert(certs, key)
            .map_err(to_js_error)?;
        config.alpn_protocols.push(b"http/1.1".to_vec());

        let conn = ServerConnection::new(Arc::new(config)).map_err(to_js_error)?;
        Ok(Self { conn })
    }

    pub fn process_tls(&mut self, input: &[u8]) -> Result<JsValue, JsValue> {
        let mut input = Cursor::new(input);
        self.conn.read_tls(&mut input).map_err(to_js_error)?;
        self.conn.process_new_packets().map_err(to_js_error)?;
        self.collect_step()
    }

    pub fn write_plaintext(&mut self, plaintext: &[u8], close: bool) -> Result<JsValue, JsValue> {
        self.conn.writer().write_all(plaintext).map_err(to_js_error)?;
        if close {
            self.conn.send_close_notify();
        }
        self.collect_step()
    }
}

impl TlsServer {
    fn collect_step(&mut self) -> Result<JsValue, JsValue> {
        let mut plaintext = Vec::new();
        let mut chunk = [0u8; 4096];
        loop {
            match self.conn.reader().read(&mut chunk) {
                Ok(0) => break,
                Ok(n) => plaintext.extend_from_slice(&chunk[..n]),
                Err(error) if error.kind() == ErrorKind::WouldBlock => break,
                Err(error) => return Err(to_js_error(error)),
            }
        }

        let mut tls = Vec::new();
        while self.conn.wants_write() {
            self.conn.write_tls(&mut tls).map_err(to_js_error)?;
        }

        let obj = Object::new();
        Reflect::set(
            &obj,
            &JsValue::from_str("plaintext"),
            &Uint8Array::from(plaintext.as_slice()).into(),
        )?;
        Reflect::set(
            &obj,
            &JsValue::from_str("tls"),
            &Uint8Array::from(tls.as_slice()).into(),
        )?;
        Reflect::set(
            &obj,
            &JsValue::from_str("handshaking"),
            &JsValue::from_bool(self.conn.is_handshaking()),
        )?;
        Ok(obj.into())
    }
}

fn parse_certs(cert_pem: &str) -> Result<Vec<CertificateDer<'static>>, JsValue> {
    let mut cursor = Cursor::new(cert_pem.as_bytes());
    let certs = rustls_pemfile::certs(&mut cursor)
        .collect::<Result<Vec<_>, _>>()
        .map_err(to_js_error)?;
    if certs.is_empty() {
        return Err(JsValue::from_str("certificate chain is empty"));
    }
    Ok(certs)
}

fn parse_private_key(key_pem: &str) -> Result<PrivateKeyDer<'static>, JsValue> {
    let mut cursor = Cursor::new(key_pem.as_bytes());
    rustls_pemfile::private_key(&mut cursor)
        .map_err(to_js_error)?
        .ok_or_else(|| JsValue::from_str("private key is missing"))
}

fn to_js_error(error: impl std::fmt::Display) -> JsValue {
    JsValue::from_str(&error.to_string())
}
