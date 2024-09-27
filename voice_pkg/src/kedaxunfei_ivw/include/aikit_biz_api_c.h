//
// Created by chaoxu8 on 2021/07/01.
//

#ifndef AIKIT_BIZ_API_C_H
#define AIKIT_BIZ_API_C_H

#ifndef __cplusplus
#include <stdbool.h>
#endif
#include "aikit_biz_type.h"
// #include "../api_aee/aee_biz_api_c.h"

#ifndef AEE_BIZ_API_C_H
// 构造器类型
typedef enum BuilderType_ {
    BUILDER_TYPE_PARAM,       // 参数输入
    BUILDER_TYPE_DATA         // 数据输入
} BuilderType;

// 构造器输入数据类型
typedef enum BuilderDataType_ {
    DATA_TYPE_TEXT,           // 文本
    DATA_TYPE_AUDIO,          // 音频
    DATA_TYPE_IMAGE,          // 图片
    DATA_TYPE_VIDEO           // 视频
} BuilderDataType;
// 构造器输入数据结构体
typedef struct BuilderData_ {
    int type;                 // 数据类型
    const char* name;         // 数据段名
    void* data;               // 数据段实体（当送入路径时，此处传入路径地址字符串指针即可；
                              //            当送入文件句柄时，此处传入文件句柄指针即可）
    int len;                  // 数据段长度（当送入路径或文件句柄时，此处传0即可）
    int status;               // 数据段状态，参考AIKIT_DataStatus枚举
} BuilderData;
#endif

// 构造器上下文及句柄
typedef struct AIKITBuilderContext_ {
    void* builderInst;        // 构造器内部类句柄
    BuilderType type;         // 构造器类型
} AIKITBuilderContext, *AIKITBuilderHandle;


#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief 初始化输入构造器
 * @param type 构造器类型
 * @return 构造器句柄，失败返回nullptr
 */
AIKITAPI AIKITBuilderHandle AIKITBuilder_Create(BuilderType type);
typedef AIKITBuilderHandle(*AIKITBuilder_Create_Ptr)(BuilderType type);

/**
 * @brief 添加整型参数
 * @param handle 构造器句柄
 * @param name 参数名称
 * @param value 参数值
 * @return 结果错误码，0=成功
 */
AIKITAPI int AIKITBuilder_AddInt(AIKITBuilderHandle handle, const char *key, int value);
typedef int(*AIKITBuilder_AddInt_Ptr)(AIKITBuilderHandle handle, const char *key, int value);

/**
 * @brief 添加字符串型参数
 * @param handle 构造器句柄
 * @param name 参数名称
 * @param str 参数值
 * @param len 字符串长度
 * @return 结果错误码，0=成功
 */
AIKITAPI int AIKITBuilder_AddString(AIKITBuilderHandle handle, const char *key, const char *value, int len);
typedef int(*AIKITBuilder_AddString_Ptr)(AIKITBuilderHandle handle, const char *key, const char *value, int len);

/**
 * @brief 添加布尔型参数
 * @param handle 构造器句柄
 * @param name 参数名称
 * @param value 参数值
 * @return 结果错误码，0=成功
 */
AIKITAPI int AIKITBuilder_AddBool(AIKITBuilderHandle handle, const char *key, bool value);
typedef int(*AIKITBuilder_AddBool_Ptr)(AIKITBuilderHandle handle, const char *key, bool value);

/**
 * @brief 添加浮点型参数
 * @param handle 构造器句柄
 * @param name 参数名称
 * @param value 参数值
 * @return 结果错误码，0=成功
 */
AIKITAPI int AIKITBuilder_AddDouble(AIKITBuilderHandle handle, const char *key, double value);
typedef int(*AIKITBuilder_AddDouble_Ptr)(AIKITBuilderHandle handle, const char *key, double value);

/**
 * @brief 添加输入数据
 * @param handle 构造器句柄
 * @param data 数据结构体实例
 * @return 结果错误码，0=成功
 */
AIKITAPI int AIKITBuilder_AddBuf(AIKITBuilderHandle handle, BuilderData *data);
typedef int(*AIKITBuilder_AddBuf_Ptr)(AIKITBuilderHandle handle, BuilderData *data);

/**
 * @brief 添加输入数据（以路径方式）
 * @param handle 构造器句柄
 * @param data 数据结构体实例
 * @return 结果错误码，0=成功
 */
AIKITAPI int AIKITBuilder_AddPath(AIKITBuilderHandle handle, BuilderData *data);
typedef int(*AIKITBuilder_AddPath_Ptr)(AIKITBuilderHandle handle, BuilderData *data);

/**
 * @brief 添加输入数据（以文件对象方式）
 * @param handle 构造器句柄
 * @param data 数据结构体实例
 * @return 结果错误码，0=成功
 */
AIKITAPI int AIKITBuilder_AddFile(AIKITBuilderHandle handle, BuilderData *data);
typedef int(*AIKITBuilder_AddFile_Ptr)(AIKITBuilderHandle handle, BuilderData *data);

/**
 * @brief 构建输入参数
 * @param handle 构造器句柄
 * @return 参数结构化指针，失败返回nullptr
 */
AIKITAPI AIKIT_BizParam* AIKITBuilder_BuildParam(AIKITBuilderHandle handle);
typedef AIKIT_BizParam*(*AIKITBuilder_BuildParam_Ptr)(AIKITBuilderHandle handle);

/**
 * @brief 构建输入数据
 * @param handle 构造器句柄
 * @return 数据结构化指针，失败返回nullptr
 */
AIKITAPI AIKIT_InputData* AIKITBuilder_BuildData(AIKITBuilderHandle handle);
typedef AIKIT_InputData*(*AIKITBuilder_BuildData_Ptr)(AIKITBuilderHandle handle);

/**
 * @brief 清空输入构造器
 * @param handle 构造器句柄
 * @return 无
 */
AIKITAPI void AIKITBuilder_Clear(AIKITBuilderHandle handle);
typedef void(*AIKITBuilder_Clear_Ptr)(AIKITBuilderHandle handle);

/**
 * @brief 销毁输入构造器
 * @param handle 构造器句柄
 * @return 无
 */
AIKITAPI void AIKITBuilder_Destroy(AIKITBuilderHandle handle);
typedef void(*AIKITBuilder_Destroy_Ptr)(AIKITBuilderHandle handle);

/**
 * SDK初始化函数用以初始化整个SDK
 * @param param  SDK配置参数
 * @return 结果错误码，0=成功
 */
AIKITAPI int32_t AIKIT_Init(AIKIT_InitParam* param);
typedef int32_t(*AIKIT_Init_Ptr)(AIKIT_InitParam* param);

/** 
 * SDK逆初始化函数用以释放SDK所占资源
 * @return 结果错误码，0=成功
 */
AIKITAPI int32_t AIKIT_UnInit();
typedef int32_t(*AIKIT_UnInit_Ptr)();

/**
 * 注册回调函数用以返回执行结果
 * @param onOutput  能力实际输出回调
 * @param onEvent   能力执行事件回调
 * @param onError   能力执行错误回调
 * @return 结果错误码，0=成功
 */
AIKITAPI int32_t AIKIT_RegisterCallback(AIKIT_Callbacks cbs);
typedef int32_t(*AIKIT_RegisterCallback_Ptr)(AIKIT_Callbacks cbs);

/**
 * 注册回调函数用以返回执行结果
 * @param ability   [in]  能力唯一标识
 * @param onOutput  能力实际输出回调
 * @param onEvent   能力执行事件回调
 * @param onError   能力执行错误回调
 * @return 结果错误码，0=成功
 */
AIKITAPI int32_t AIKIT_RegisterAbilityCallback(const char* ability, AIKIT_Callbacks cbs);
typedef int32_t(*AIKIT_RegisterAbilityCallback_Ptr)(const char* ability, AIKIT_Callbacks cbs);

/**
 * 初始化能力引擎
 * @param ability   [in]  能力唯一标识
 * @param param     [in] 初始化参数
 * @return 错误码 0=成功，其他表示失败
 */
AIKITAPI int32_t AIKIT_EngineInit(const char* ability, AIKIT_BizParam* param);
typedef int32_t(*AIKIT_EngineInit_Ptr)(const char* ability, AIKIT_BizParam* param);

/**
 * 能力引擎逆初始化
 * @param ability   [in]  能力唯一标识
 * @return 错误码 0=成功，其他表示失败
 */
AIKITAPI int32_t AIKIT_EngineUnInit(const char* ability);
typedef int32_t(*AIKIT_EngineUnInit_Ptr)(const char* ability);

/**
 * 个性化数据预处理
 * @param   ability     [in]  能力唯一标识
 * @param   srcData     [in]  原始数据输入
 * @param   data        [out] 结果数据输出
 * @return 错误码 0=成功，其他表示失败
 */
AIKITAPI int32_t AIKIT_PreProcess(const char* ability, AIKIT_CustomData* srcData, AIKIT_CustomData** data);
typedef int32_t(*AIKIT_PreProcess_Ptr)(const char* ability, AIKIT_CustomData* srcData, AIKIT_CustomData** data);

/**
 * 个性化数据加载
 * @param ability    能力唯一标识
 * @param data      个性化数据
 * @return 错误码 0=成功，其他表示失败
 */
AIKITAPI int32_t AIKIT_LoadData(const char* ability, AIKIT_CustomData* data);
typedef int32_t(*AIKIT_LoadData_Ptr)(const char* ability, AIKIT_CustomData* data);

/**
 * 个性化数据加载
 * @param  ability      能力唯一标识
 * @param  key          个性化数据唯一标识
 * @param  index        个性化数据索引
 * @return 错误码 0=成功，其他表示失败
 */
AIKITAPI int32_t AIKIT_UnLoadData(const char* ability, const char* key, int index);
typedef int32_t(*AIKIT_UnLoadData_Ptr)(const char* ability, const char* key, int index);

/**
 * 指定要使用的个性化数据集合，未调用，则默认使用所有AIKIT_LoadData加载的数据
 * 可调用多次以使用不同key集合
 * @param  abilityId  能力唯一标识
 * @param  key        个性化数据唯一标识数组
 * @param  index      个性化数据索引数组
 * @param  count      个性化数据索引数组成员个数
 * @return 错误码 0=成功，其他表示失败
 */
AIKITAPI int32_t  AIKIT_SpecifyDataSet(const char* ability, const char* key, int index[], int count);
typedef int32_t(*AIKIT_SpecifyDataSet_Ptr)(const char* ability, const char* key, int index[], int count);

/**
 * 启动one-shot模式能力同步模式调用
 * @param   ability    能力唯一标识
 * @param   param      能力参数
 * @param   inputData  能力数据输入
 * @param   outputData 能力数据输出
 * @return 错误码 0=成功，其他表示失败
 */
AIKITAPI int32_t AIKIT_OneShot(const char* ability, AIKIT_BizParam* params, AIKIT_InputData* inputData, AIKIT_OutputData** outputData);
typedef int32_t(*AIKIT_OneShot_Ptr)(const char* ability, AIKIT_BizParam* params, AIKIT_InputData* inputData, AIKIT_OutputData** outputData);


/**
 * 启动one-shot模式能力异步模式调用
 * @param ability    能力唯一标识d
 * @param param      能力参数
 * @param data       能力数据输入
 * @param usrContext 上下文指针
 * @param outHandle  生成的引擎会话句柄
 * @return 错误码 0=成功，其他表示失败
 */
AIKITAPI int32_t AIKIT_OneShotAsync(const char* ability, AIKIT_BizParam* params, AIKIT_InputData* data, void* usrContext, AIKIT_HANDLE** outHandle);
typedef int32_t(*AIKIT_OneShotAsync_Ptr)(const char* ability, AIKIT_BizParam* params, AIKIT_InputData* data, void* usrContext, AIKIT_HANDLE** outHandle);

/**
 * 启动会话模式能力调用实例，若引擎未初始化，则内部首先完成引擎初始化
 * @param ability   能力唯一标识
 * @param len       ability长度
 * @param param     初始化参数
 * @param usrContext上下文指针
 * @param outHandle 生成的引擎会话句柄
 * @return 错误码 0=成功，其他表示失败
 */
AIKITAPI int32_t AIKIT_Start(const char* ability, AIKIT_BizParam* param, void* usrContext, AIKIT_HANDLE** outHandle);
typedef int32_t(*AIKIT_Start_Ptr)(const char* ability, AIKIT_BizParam* param, void* usrContext, AIKIT_HANDLE** outHandle);

/**
 * 会话模式输入数据
 * @param handle    会话实例句柄
 * @param input     输入数据
 * @return 结果错误码，0=成功
 */
AIKITAPI int32_t AIKIT_Write(AIKIT_HANDLE* handle, AIKIT_InputData* input);
typedef int32_t(*AIKIT_Write_Ptr)(AIKIT_HANDLE* handle, AIKIT_InputData* input);

/**
 * 会话模式同步读取数据
 * @param handle    会话实例句柄
 * @param output     输入数据
 * @return 结果错误码，0=成功
 * @note  output内存由SDK自行维护,无需主动释放
 */
AIKITAPI int32_t AIKIT_Read(AIKIT_HANDLE* handle, AIKIT_OutputData** output);
typedef int32_t(*AIKIT_Read_Ptr)(AIKIT_HANDLE* handle, AIKIT_OutputData** output);

/**
 * 结束会话实例
 * @param handle    会话实例句柄
 * @return 结果错误码，0=成功
 */
AIKITAPI int32_t AIKIT_End(AIKIT_HANDLE* handle);
typedef int32_t(*AIKIT_End_Ptr)(AIKIT_HANDLE* handle);


/**
 * 释放能力占用资源
 * @param   ability    能力唯一标识
 * @return 错误码 0=成功，其他表示失败
 */
AIKITAPI int32_t AIKIT_FreeAbility(const char* ability);
typedef int32_t(*AIKIT_FreeAbility_Ptr)(const char* ability);

/**
 * 设置日志级别
 * @param  level    日志级别
 * @return 错误码 0=成功，其他表示失败
*/
AIKITAPI int32_t AIKIT_SetLogLevel(int32_t level);
typedef int32_t(*AIKIT_SetLogLevel_Ptr)(int32_t level);

/**
 * 设置日志输出模式
 * @param  mode    日志输出模式
 * @return 错误码 0=成功，其他表示失败
*/
AIKITAPI int32_t AIKIT_SetLogMode(int32_t mode);
typedef int32_t(*AIKIT_SetLogMode_Ptr)(int32_t mode);

/**
 * 输出模式为文件时，设置日志文件名称
 * @param  path    日志名称
 * @return 错误码 0=成功，其他表示失败
*/
AIKITAPI int32_t AIKIT_SetLogPath(const char* path);
typedef int32_t(*AIKIT_SetLogPath_Ptr)(const char* path);

/** 
 * 获取设备ID
 * @param deviceID    设备指纹输出字符串
 * @return 结果错误码，0=成功
 */
AIKITAPI int32_t AIKIT_GetDeviceID(const char** deviceID);
typedef int32_t(*AIKIT_GetDeviceID_Ptr)(const char** deviceID);

/** 
 * 设置授权更新间隔，单位为秒，默认为300秒
 * AIKIT_Init前设置
 * @param interval    间隔秒数
 * @return 结果错误码，0=成功
 */
AIKITAPI int32_t AIKIT_SetAuthCheckInterval(uint32_t interval);
typedef int32_t(*AIKIT_SetAuthCheckInterval_Ptr)(uint32_t interval);

/** 
 * 获取SDK版本号
 * @return SDK版本号
 */
AIKITAPI const char* AIKIT_GetVersion();
typedef const char*(*AIKIT_GetVersion_Ptr)();

/**
 * @brief 获取能力对应的引擎版本
 * 
 * @param ability 能力唯一标识
 * @return const* 引擎版本号
 */
AIKITAPI const char* AIKIT_GetEngineVersion(const char* ability);
typedef const char*(*AIKIT_GetEngineVersion_Ptr)(const char* ability);

/**
 * 本地日志是否开启
 * @param open
 * @return
 */
AIKITAPI int32_t AIKIT_SetILogOpen(bool open);
typedef int32_t(*AIKIT_SetILogOpenPtr)(bool open);

/**
 * 本地日志最大存储个数（【1，300】）
 * @param count
 * @return
 */
AIKITAPI int32_t AIKIT_SetILogMaxCount(uint32_t count);
typedef int32_t(*AIKIT_SetILogMaxCountPtr)(uint32_t count);

/**
 * 设置单日志文件大小（(0，10M】）
 * @param bytes
 * @return
 */
AIKITAPI int32_t AIKIT_SetILogMaxSize(long long bytes);
typedef int32_t(*AIKIT_SetILogMaxSizePtr)(long long bytes);

/**
 * 设置SDK相关配置
 * @param key    参数名字
 * @param value  参数值
 * @return 结果错误码，0=成功
 */
AIKITAPI int32_t AIKIT_SetConfig(const char* key, const void* value);
typedef int32_t(*AIKIT_SetConfigPtr)(const char* key, const void* value);

/**
 * 设置SDK内存模式
 * @param ability 能力id
 * @param mode    模式，取值参见 AIKIT_MEMORY_MODE
 * @return AIKITAPI 
 */
AIKITAPI int32_t AIKIT_SetMemoryMode(const char* ability,int32_t mode);
typedef int32_t(*AIKIT_SetMemoryModePtr)(const char* ability,int32_t mode);

/**
 * 设置日志级别，模式，以及保存路径,旧版日志接口，不推荐使用
 * @param  level    日志级别
 * @param  mode     日志输出模式
 * @param  level    输出模式为文件时的文件名称
 * @return 错误码 0=成功，其他表示失败
 */
AIKITAPI int32_t AIKIT_SetLogInfo(int32_t level, int32_t mode, const char* path);
typedef int32_t(*AIKIT_SetLogInfo_Ptr)(int32_t level, int32_t mode, const char* path);

#ifdef __cplusplus
}
#endif

#endif  // AIKIT_BIZ_API_C_H
