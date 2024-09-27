#include <fstream>
#include <iostream>
#include <assert.h>
#include <cstring>
#include <atomic>
#include <unistd.h>

#include "./include/aikit_biz_api.h"
#include "./include/aikit_constant.h"
#include "./include/aikit_biz_config.h"
#include "./include/linuxrec.h"

#include <signal.h>

#include "ros/ros.h"
#include "std_msgs/String.h"
#include "voice_pkg/VoiceSrv.h"

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
#define E_SR_NOMEM			    2
#define E_SR_INVAL			    3
#define E_SR_RECORDFAIL			4
#define E_SR_ALREADY			5


int times = 1;
struct recorder *recorder;

void sleep_ms(int ms)
{
    usleep(ms * 1000);
}


// 结束ctrl-c的信号

bool app_stopped = false;
bool process_flag = false;

void sigint_handler(int sig){
    printf("hihihi");
    if(sig == SIGINT){
        // ctrl+c退出时执行的代码
        std::cout << "ctrl+c pressed!" << std::endl;
        app_stopped = true;
    }
}

ros::Publisher ivw_chatter_pub;
// ros::Publisher iat_chatter_pub;
// ros::ServiceClient iatclient;

//唤醒结果通过此回调函数输出
void OnOutput(AIKIT_HANDLE* handle, const AIKIT_OutputData* output){
    string temp = (char *)output->node->value;
    if(temp.find("小红小红") != string::npos)
    {
        printf("----触发小红小红----\n");
        std_msgs::String msg;
        msg.data = "小红小红";
        ROS_INFO("ivw: %s", msg.data.c_str());
        ivw_chatter_pub.publish(msg);
        process_flag = true;
        return;
    }
    if(temp.find("别说了") != string::npos)
    {
        printf("----触发别说了----\n");
        process_flag = true;
        return;
    }

    // printf("OnOutput abilityID :%s\n",handle->abilityID);
    // printf("OnOutput key:%s\n",output->node->key);
    // printf("OnOutput value:%s\n",(char*)output->node->value);
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

    // cout << "buffer is: " << dataBuf << endl;
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
    wavfmt.nChannels = 1;
    wavfmt.nSamplesPerSec = SAMPLE_RATE_16K;
    wavfmt.nAvgBytesPerSec = wavfmt.nBlockAlign * wavfmt.nSamplesPerSec;

    //加载自定义的唤醒词
    if (times == 1){
        AIKIT_CustomData customData;
        customData.key = "key_word";
        customData.index = 0;
        customData.from = AIKIT_DATA_PTR_PATH;
        customData.value =(void*)"/home/kuavo/catkin_dt/src/voice_pkg/src/kedaxunfei_ivw/resource/keyword-nhxd.txt";
        customData.len = strlen("/home/kuavo/catkin_dt/src/voice_pkg/src/kedaxunfei_ivw/resource/keyword-nhxd.txt");
        customData.next = nullptr;
        customData.reserved = nullptr;
        printf("AIKIT_LoadData start!\n");
        ret = AIKIT_LoadData("e867a88f2", &customData);
        printf("AIKIT_LoadData end!\n");
        printf("AIKIT_LoadData:%d\n",ret);
        if(ret != 0){
            goto exit;
        }
        times++;
    }

    //指定要使用的个性化数据集合，未调用，则默认使用所有loadData加载的数据。
    ret = AIKIT_SpecifyDataSet("e867a88f2", "key_word",index,1);
    printf("AIKIT_SpecifyDataSet:%d\n",ret);
    if(ret != 0){
        goto  exit;
    }

	// 设置门限值：直接在keyword-nhxd.txt设置就行 门限值最小:0,最大:1024。值越低越模糊，越低越容易唤醒
    // paramBuilder->param("wdec_param_nCmThreshold","0 0:999",8);
    // 更新自定义唤醒词
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


    // 无限循环
    while (ros::ok()) {
        sleep_ms(200); //阻塞直到唤醒结果出现
        printf("Listening...\n");
        count++;

        if (app_stopped){
      			break;
        }
        if (process_flag){
            // 请求iat服务
            // printf("----请求iat服务----\n");
            // std::string iatresult;
            // voice_pkg::VoiceSrv voicesrv;
            // voicesrv.request.input = "from ivw";
            // if (iatclient.call(voicesrv)) {
            //     iatresult = voicesrv.response.output;
            //     std::cout << "output:" << iatresult << endl;
            //     ROS_INFO("iat res: %s", voicesrv.response.output);
            // }
            // else {
            //     ROS_ERROR("Failed to call service kedaxunfei iat");
            //     iatresult = "";
            // }
            // std_msgs::String msg;
            // msg.data = iatresult;
            // ROS_INFO("%s", msg.data.c_str());
            // iat_chatter_pub.publish(msg);
            process_flag = false;
        }

        if (count % 20 == 0)	//为了防止循环监听时写入到缓存中的数据过大
        {
            //先释放当前录音资源
            stop_record(recorder);
            close_recorder(recorder);
            destroy_recorder(recorder);
            recorder = NULL;
            // printf("防止音频资源过大，重建\n");
            // struct recorder *recorder;
            //重建录音资源
            err_code = create_recorder(&recorder, iat_cb, (void*)handle);
            err_code = open_recorder(recorder, get_default_input_dev(), &wavfmt);
            err_code = start_record(recorder);
        }
    }
    //先释放当前录音资源
    stop_record(recorder);
    close_recorder(recorder);
    destroy_recorder(recorder);
    recorder = NULL;

    ret = AIKIT_End(handle);

 exit:
    if(paramBuilder != nullptr){
        delete paramBuilder;
        paramBuilder = nullptr;
    }
}

std::string getValueForKey(const std::string& jsonString, const std::string& key) {
    size_t found = jsonString.find("\"" + key + "\":");
    if (found != std::string::npos) {
        size_t start = found + key.length() + 4;
        size_t end = jsonString.find_first_of("\",}", start);
        if (end != std::string::npos) {
            return jsonString.substr(start, end - start);
        }
    }
    return ""; // 如果未找到，返回空字符串
}
void TestIVW(){

    // 打开 JSON 文件
    std::ifstream file("/home/kuavo/catkin_dt/config_dt.json");

    std::string line;
    std::string jsonContent;

    // 逐行读取 JSON 文件内容
    while (std::getline(file, line)) {
        jsonContent += line;
    }

    // 关闭文件
    file.close();

    // 想要查找的键
    std::string mic_appID_Key = "mic_appID";
    std::string mic_apiKey_Key = "mic_apiKey";
    std::string mic_apiSecret_Key = "mic_apiSecret";
    // 查找键对应的值
    std::string mic_appID = getValueForKey(jsonContent, mic_appID_Key);
    std::string mic_apiKey = getValueForKey(jsonContent, mic_apiKey_Key);
    std::string mic_apiSecret = getValueForKey(jsonContent, mic_apiSecret_Key);
    std::cout << "mic_appID" << mic_appID << std::endl;
    std::cout << "mic_apiKey" << mic_apiKey << std::endl;
    std::cout << "mic_apiSecret" << mic_apiSecret << std::endl;

    AIKIT_Configurator::builder()
                        .app()
                            .appID(mic_appID.c_str())
                            .apiKey(mic_apiKey.c_str())
                            .apiSecret(mic_apiSecret.c_str())
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



int main(int argc, char **argv) {
    // 创建信号
  	signal(SIGINT, sigint_handler);


    ros::init(argc, argv, "ivw_node");
    ros::NodeHandle n;
    ivw_chatter_pub = n.advertise<std_msgs::String>("ivw_chatter", 1);
    // iat_chatter_pub = n.advertise<std_msgs::String>("iat_chatter", 1);

    // iatclient = n.serviceClient<voice_pkg::VoiceSrv>("kedaxunfei_iat");

    TestIVW();
    return 0;
}

