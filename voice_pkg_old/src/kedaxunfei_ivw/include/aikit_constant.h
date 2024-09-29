/*
 * @Description: 
 * @version: 
 * @Author: xkzhang9
 * @Date: 2020-10-28 10:20:45
 * @LastEditors: rfge
 * @LastEditTime: 2020-12-28 11:14:20
 */

#ifndef AIKIT_CONSTANT_H
#define AIKIT_CONSTANT_H

typedef enum {
    LOG_STDOUT = 0,
    LOG_LOGCAT,
    LOG_FILE,
} AIKIT_LOG_MODE;

typedef enum {
    LOG_LVL_VERBOSE,
    LOG_LVL_DEBUG,
    LOG_LVL_INFO,
    LOG_LVL_WARN,
    LOG_LVL_ERROR,
    LOG_LVL_CRITICAL,
    LOG_LVL_OFF = 100,

} AIKIT_LOG_LEVEL;

typedef enum {
    MEMORY_FULL_MODE,
    MEMORY_FRIENDLY_MODE
} AIKIT_MEMORY_MODE;

#endif  //AIKIT_CONSTANT_H
