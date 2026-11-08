#!/usr/bin/env python3
"""Offline: emit the JSON contract and deliberately unapproved fill-in template."""
import json
from pathlib import Path
import recovery_control as c

out = Path(__file__).resolve().parent
hash_type = dict(type='string', pattern='^[0-9a-f]{64}$')

def obj(properties):
    return dict(type='object', properties=properties, required=list(properties), additionalProperties=False)

schema = obj(dict(
    schema_version=dict(const=1), profile=dict(const=c.PROFILE), target=dict(const=c.TARGET),
    candidate=obj(dict(path=dict(type='string', minLength=1), bytes=dict(type='integer', minimum=2048, maximum=c.SIZE),
                       sha256=hash_type, wrapped_kernel_sha256=dict(const=c.KERNEL_HASH), header_page_sha256=hash_type)),
    padding=obj(dict(kind=dict(const='constant-byte'), byte=dict(type='integer', minimum=0, maximum=255),
                     full_partition_sha256=hash_type)),
    review=obj(dict(approved=dict(const=True), reviewer=dict(type='string', minLength=1, maxLength=1000),
                    reference=dict(type='string', minLength=1, maxLength=1000),
                    marker=dict(type='string', minLength=1, maxLength=1000),
                    bounded_return_seconds=dict(type='integer', minimum=1, maximum=600),
                    ram_only_no_persistent_mounts_or_writes=dict(const=True),
                    manual_recovery_and_normal_boot=dict(const=True)))))
schema.update({'$schema': 'https://json-schema.org/draft/2020-12/schema',
               'title': 'Reviewed ASUS recovery stock-kernel control v1'})
template = dict(schema_version=1, profile=c.PROFILE, target=c.TARGET,
                candidate=dict(path='REVIEW_REQUIRED-relative-path-to-control.img', bytes=0,
                               sha256='REVIEW_REQUIRED', wrapped_kernel_sha256=c.KERNEL_HASH,
                               header_page_sha256='REVIEW_REQUIRED'),
                padding=dict(kind='constant-byte', byte=0, full_partition_sha256='REVIEW_REQUIRED'),
                review=dict(approved=False, reviewer='REVIEW_REQUIRED', reference='REVIEW_REQUIRED',
                            marker='REVIEW_REQUIRED', bounded_return_seconds=0,
                            ram_only_no_persistent_mounts_or_writes=False, manual_recovery_and_normal_boot=False))
for name, value in [('manifest.schema.json', schema), ('manifest.UNAPPROVED.template.json', template)]:
    (out / name).write_text(json.dumps(value, indent=2) + '\n')
