# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: kvs.proto
# Protobuf Python Version: 5.29.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    29,
    0,
    '',
    'kvs.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\tkvs.proto\x12\x03kvs\"5\n\x05Tupla\x12\r\n\x05\x63have\x18\x01 \x01(\t\x12\r\n\x05valor\x18\x02 \x01(\t\x12\x0e\n\x06versao\x18\x03 \x01(\x05\"*\n\nChaveValor\x12\r\n\x05\x63have\x18\x01 \x01(\t\x12\r\n\x05valor\x18\x02 \x01(\t\"<\n\x0b\x43haveVersao\x12\r\n\x05\x63have\x18\x01 \x01(\t\x12\x13\n\x06versao\x18\x02 \x01(\x05H\x00\x88\x01\x01\x42\t\n\x07_versao\"\x18\n\x06Versao\x12\x0e\n\x06versao\x18\x01 \x01(\x05\x32\xce\x02\n\x03KVS\x12(\n\x06Insere\x12\x0f.kvs.ChaveValor\x1a\x0b.kvs.Versao\"\x00\x12*\n\x08\x43onsulta\x12\x10.kvs.ChaveVersao\x1a\n.kvs.Tupla\"\x00\x12)\n\x06Remove\x12\x10.kvs.ChaveVersao\x1a\x0b.kvs.Versao\"\x00\x12\x32\n\x0cInsereVarias\x12\x0f.kvs.ChaveValor\x1a\x0b.kvs.Versao\"\x00(\x01\x30\x01\x12\x34\n\x0e\x43onsultaVarias\x12\x10.kvs.ChaveVersao\x1a\n.kvs.Tupla\"\x00(\x01\x30\x01\x12\x33\n\x0cRemoveVarias\x12\x10.kvs.ChaveVersao\x1a\x0b.kvs.Versao\"\x00(\x01\x30\x01\x12\'\n\x08Snapshot\x12\x0b.kvs.Versao\x1a\n.kvs.Tupla\"\x00\x30\x01\x42\x1b\n\x17\x62r.ufu.facom.gbc074.kvsP\x01\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'kvs_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  _globals['DESCRIPTOR']._loaded_options = None
  _globals['DESCRIPTOR']._serialized_options = b'\n\027br.ufu.facom.gbc074.kvsP\001'
  _globals['_TUPLA']._serialized_start=18
  _globals['_TUPLA']._serialized_end=71
  _globals['_CHAVEVALOR']._serialized_start=73
  _globals['_CHAVEVALOR']._serialized_end=115
  _globals['_CHAVEVERSAO']._serialized_start=117
  _globals['_CHAVEVERSAO']._serialized_end=177
  _globals['_VERSAO']._serialized_start=179
  _globals['_VERSAO']._serialized_end=203
  _globals['_KVS']._serialized_start=206
  _globals['_KVS']._serialized_end=540
# @@protoc_insertion_point(module_scope)
