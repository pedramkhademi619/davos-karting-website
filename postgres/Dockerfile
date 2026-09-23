# syntax=docker/dockerfile:1.7
#
# PostgreSQL 16.4 (Alpine) with the pgvector extension, used by the semantic answer cache.
#
# Why not the official pgvector image: that one is Debian (glibc). The development database volume was created by
# postgres:16.4-alpine (musl), and switching libc under an existing data directory changes text collation, which
# silently invalidates text indexes. This image keeps the exact same base and only adds the extension files.

# ---- build the extension against the very same Postgres it will run in ------------------------------
FROM postgres:16.4-alpine AS build
ARG PGVECTOR_VERSION=0.8.0
# SHA-256 of https://github.com/pgvector/pgvector/archive/refs/tags/v0.8.0.tar.gz (checked below, so a changed
# or tampered download fails the build).
ARG PGVECTOR_SHA256=867a2c328d4928a5a9d6f052cd3bc78c7d60228a9b914ad32aa3db88e9de27b0
RUN apk add --no-cache build-base wget \
 && wget -q -O /tmp/pgvector.tar.gz "https://github.com/pgvector/pgvector/archive/refs/tags/v${PGVECTOR_VERSION}.tar.gz" \
 && echo "${PGVECTOR_SHA256}  /tmp/pgvector.tar.gz" | sha256sum -c - \
 && tar -xzf /tmp/pgvector.tar.gz -C /tmp \
 && cd "/tmp/pgvector-${PGVECTOR_VERSION}" \
 # with_llvm=no: Postgres is built with JIT support, which would need clang for optional bitcode files.
 && make with_llvm=no OPTFLAGS="" \
 && make install with_llvm=no

# ---- runtime: the untouched official image plus three kinds of files -----------------------------------
FROM postgres:16.4-alpine
COPY --from=build /usr/local/lib/postgresql/vector.so /usr/local/lib/postgresql/vector.so
COPY --from=build /usr/local/share/postgresql/extension/vector.control /usr/local/share/postgresql/extension/
COPY --from=build /usr/local/share/postgresql/extension/vector--*.sql /usr/local/share/postgresql/extension/
