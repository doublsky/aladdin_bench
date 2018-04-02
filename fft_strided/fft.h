#include <stdio.h>
#include <stdlib.h>
#include "support.h"

//#define FFT_SIZE 1024
#define twoPI 6.28318530717959
#define DTYPE int32_t
#define IS_DTYPE_FXP 1
#define Q 16

void fft(DTYPE real[FFT_SIZE], DTYPE img[FFT_SIZE], DTYPE real_twid[FFT_SIZE/2], DTYPE img_twid[FFT_SIZE/2]);


////////////////////////////////////////////////////////////////////////////////
// Test harness interface code.

struct bench_args_t {
        DTYPE real[FFT_SIZE];
        DTYPE img[FFT_SIZE];
        DTYPE real_twid[FFT_SIZE/2];
        DTYPE img_twid[FFT_SIZE/2];
};
