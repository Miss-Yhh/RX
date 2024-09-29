#include <fstream>
#include <assert.h>
#include <cstring>
#include <atomic>
#include <unistd.h>

#include "./include/aikit_biz_api.h"
#include "./include/aikit_constant.h"
#include "./include/aikit_biz_config.h"
#include "./include/linuxrec.h"

using namespace std;
using namespace AIKIT;

#define SAMPLE_RATE_16K (16000)
#define DEFAULT_FORMAT		\
{\
        WAVE_FORMAT_PCM,	\
        1,			\
        16000,			\
        32000,			\
        2,			\
        16,			\
        sizeof(WAVEFORMATEX)	\
}
#define E_SR_NOACTIVEDEVICE		1
#define E_SR_NOMEM			2
#define E_SR_INVAL			3
#define E_SR_RECORDFAIL			4
#define E_SR_ALREADY			5


int times = 1;
struct recorder *recorder;

void sleep_ms(int ms)
{
        usleep(ms * 1000);
}

//唤醒结果通过此回调函数输出
void OnOutput(AIKIT_HANDLE* handle, const AIKIT_OutputData* output){
    string temp = (char *)output->node->value;
    if( temp.find("你好小迪") != string::npos)
    {
        printf("----触发你好小迪,拦截----\n");
        return;
    }
    printf("OnOutput abilityID :%s\n",handle->abilityID);
    printf("OnOutput key:%s\n",output->node->key);
    printf("OnOutput value:%s\n",(char*)output->node->value);
}

void OnEvent(AIKIT_HANDLE* handle, AIKIT_EVENT eventType, const AIKIT_OutputEvent* eventValue){
    printf("OnEvent:%d\n",eventType);
}

void OnError(AIKIT_HANDLE* handle, int32_t err, const char* desc){
    printf("OnError:%d\n",err);
}

//读取录音内容的函数，在新线程反复运行。喂给创建录音的函数create_recorder
void iat_cb(char *dataBuf, unsigned long len, void *user_para)
{
        int errcode = 0;
        AIKIT_HANDLE* handle = (AIKIT_HANDLE*)user_para;

        if(len == 0 || dataBuf == NULL)
        {
                return;
        }
        //创建数据构造器，将音频数据加载到构造器中
        AIKIT_DataBuilder* dataBuilder = AIKIT_DataBuilder::create();
        AiAudio* wavData = AiAudio::get("wav")->data(dataBuf,len)->valid();
        dataBuilder->payload(wavData);
        //将数据构造器的内容通过AIKIT_Write写入
        int ret = AIKIT_Write(handle,AIKIT_Builder::build(dataBuilder));
        if (ret != 0) {
          printf("AIKIT_Write:%d\n",ret);
        }
}

void ivwIns(){
    AIKIT_ParamBuilder* paramBuilder = nullptr;
    AIKIT_HANDLE* handle = nullptr;
    int index[] = {0};
    int ret = 0;
    int err_code = 0;
    int count = 0;
    paramBuilder = AIKIT_ParamBuilder::create();

    WAVEFORMATEX wavfmt = DEFAULT_FORMAT;
    wavfmt.nSamplesPerSec = SAMPLE_RATE_16K;
    wavfmt.nAvgBytesPerSec = wavfmt.nBlockAlign * wavfmt.nSamplesPerSec;

    //加载自定义的唤醒词
    if (times == 1){
            AIKIT_CustomData customData;
            customData.key = "key_word";
            customData.index = 0;
            customData.from = AIKIT_DATA_PTR_PATH;
            customData.value =(void*)"./resource/keyword-nhxd.txt";
            customData.len = strlen("./resource/keyword-nhxd.txt");
            customData.next = nullptr;
            customData.reserved = nullptr;
            printf("AIKIT_LoadData start!\n");
            ret = AIKIT_LoadData("e867a88f2",&customData);
            printf("AIKIT_LoadData end!\n");
            printf("AIKIT_LoadData:%d\n",ret);
            if(ret != 0){
                    goto  exit;
            }
            times++;
        }

    //指定要使用的个性化数据集合，未调用，则默认使用所有loadData加载的数据。
    ret = AIKIT_SpecifyDataSet("e867a88f2","key_word",index,1);
    printf("AIKIT_SpecifyDataSet:%d\n",ret);
    if(ret != 0){
        goto  exit;
    }

	//0:999设置门限值，最小长度:0, 最大长度:1024。值越低越模糊
    paramBuilder->param("wdec_param_nCmThreshold","0 0:999",8);
    paramBuilder->param("gramLoad",true);
    ret = AIKIT_Start("e867a88f2",AIKIT_Builder::build(paramBuilder),nullptr,&handle);
    printf("AIKIT_Start:%d\n",ret);
    if(ret != 0){
        goto  exit;
    }
        //创建录音机
        err_code = create_recorder(&recorder, iat_cb, (void*)handle);
        if (recorder == NULL || err_code != 0) {
                        printf("create recorder failed: %d\n", err_code);
                        err_code = -E_SR_RECORDFAIL;
                        goto exit;
        }

        //打开录音机
        err_code = open_recorder(recorder, get_default_input_dev(), &wavfmt);
        if (err_code != 0) {
                printf("recorder open failed: %d\n", err_code);
                err_code = -E_SR_RECORDFAIL;
                goto exit;
        }
        err_code = start_record(recorder);
        if (err_code != 0) {
                printf("start record failed: %d\n", err_code);
                err_code = -E_SR_RECORDFAIL;
                goto exit;
        }

        //循环监听
        while (1)
        {
                sleep_ms(200); //阻塞直到唤醒结果出现
                printf("Listening...\n");
                count++;
                if (count % 20 == 0)	//为了防止循环监听时写入到缓存中的数据过大
                {
                        //先释放当前录音资源
                        stop_record(recorder);
                        close_recorder(recorder);
                        destroy_recorder(recorder);
                        recorder = NULL;
                        //printf("防止音频资源过大，重建\n");
                        //struct recorder *recorder;
                        //重建录音资源
                        err_code = create_recorder(&recorder, iat_cb, (void*)handle);
                        err_code = open_recorder(recorder, get_default_input_dev(), &wavfmt);
                        err_code = start_record(recorder);
                }
        }

    ret = AIKIT_End(handle);

 exit:
    if(paramBuilder != nullptr)
        {
        delete paramBuilder;
        paramBuilder = nullptr;
    }
}

void TestIVW(){
    AIKIT_Configurator::builder()
                        .app()
                            .appID("fe7065eb")
                            .apiKey("e6410e10f9ac4169cae3a7a1c795961d")
                            .apiSecret("NTg3NDhkMDY2MGE2ZjQ0Nzk1NzY3MDVh")
                            .workDir("./")
                        .auth()
                            .authType(0)
                            .ability("e867a88f2")
                        .log()
                            .logLevel(LOG_LVL_INFO);

	//对唤醒结果进行响应的回调函数
    AIKIT_Callbacks cbs = {OnOutput,OnEvent,OnError};
    AIKIT_RegisterAbilityCallback("e867a88f2",cbs);
    AIKIT_SetILogOpen(false);

    int ret = AIKIT_Init();
    if(ret != 0){
        printf("AIKIT_Init failed:%d\n",ret);
        goto exit;
    }

    ret = AIKIT_EngineInit("e867a88f2",nullptr);
    if(ret != 0){
        printf("AIKIT_EngineInit failed:%d\n",ret);
        goto exit;
    }

    ivwIns();

 exit:
    AIKIT_UnInit();
}

int main() {

    TestIVW();

    return 0;
}
