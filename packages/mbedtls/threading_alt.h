#ifndef MBEDTLS_THREADING_ALT_H
#define MBEDTLS_THREADING_ALT_H

#ifdef __cplusplus
extern "C" {
#endif

/* mbedtls_threading_mutex_t */
typedef struct mbedtls_threading_mutex_t
{
    void* mutex_ptr;    /* std::mutex* */
} mbedtls_threading_mutex_t;

#ifdef __cplusplus
}
#endif

#endif /* MBEDTLS_THREADING_ALT_H */
