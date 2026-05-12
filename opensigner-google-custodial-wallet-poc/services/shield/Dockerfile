FROM busybox:1.36.1-uclibc AS busybox
FROM gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.18.3 AS proxy

FROM ghcr.io/openfort-xyz/shield:v0.2.40

COPY --from=busybox /bin/busybox /busybox
COPY --from=busybox /bin/sh /bin/sh
COPY --from=proxy /cloud-sql-proxy /cloud-sql-proxy
COPY entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/busybox", "sh", "/entrypoint.sh"]
CMD ["server"]
