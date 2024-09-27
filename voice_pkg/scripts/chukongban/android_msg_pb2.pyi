from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class register_client(_message.Message):
    __slots__ = ("message_type", "client_type", "ip_address", "mac_address", "auth_token")
    MESSAGE_TYPE_FIELD_NUMBER: _ClassVar[int]
    CLIENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    MAC_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    AUTH_TOKEN_FIELD_NUMBER: _ClassVar[int]
    message_type: str
    client_type: int
    ip_address: str
    mac_address: str
    auth_token: str
    def __init__(self, message_type: _Optional[str] = ..., client_type: _Optional[int] = ..., ip_address: _Optional[str] = ..., mac_address: _Optional[str] = ..., auth_token: _Optional[str] = ...) -> None: ...

class client_request(_message.Message):
    __slots__ = ("message_type", "auth_token")
    MESSAGE_TYPE_FIELD_NUMBER: _ClassVar[int]
    AUTH_TOKEN_FIELD_NUMBER: _ClassVar[int]
    message_type: str
    auth_token: str
    def __init__(self, message_type: _Optional[str] = ..., auth_token: _Optional[str] = ...) -> None: ...

class server_reply(_message.Message):
    __slots__ = ("ret_code",)
    RET_CODE_FIELD_NUMBER: _ClassVar[int]
    ret_code: str
    def __init__(self, ret_code: _Optional[str] = ...) -> None: ...

class report_cfg(_message.Message):
    __slots__ = ("ip",)
    IP_FIELD_NUMBER: _ClassVar[int]
    ip: str
    def __init__(self, ip: _Optional[str] = ...) -> None: ...

class server_broadcast(_message.Message):
    __slots__ = ("token", "server_name", "server_ip", "server_port")
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    SERVER_NAME_FIELD_NUMBER: _ClassVar[int]
    SERVER_IP_FIELD_NUMBER: _ClassVar[int]
    SERVER_PORT_FIELD_NUMBER: _ClassVar[int]
    token: str
    server_name: str
    server_ip: str
    server_port: int
    def __init__(self, token: _Optional[str] = ..., server_name: _Optional[str] = ..., server_ip: _Optional[str] = ..., server_port: _Optional[int] = ...) -> None: ...

class reply_value(_message.Message):
    __slots__ = ("value",)
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: int
    def __init__(self, value: _Optional[int] = ...) -> None: ...

class navmap_collec(_message.Message):
    __slots__ = ("navmap_count", "filemaps")
    NAVMAP_COUNT_FIELD_NUMBER: _ClassVar[int]
    FILEMAPS_FIELD_NUMBER: _ClassVar[int]
    navmap_count: int
    filemaps: _containers.RepeatedCompositeFieldContainer[navmap]
    def __init__(self, navmap_count: _Optional[int] = ..., filemaps: _Optional[_Iterable[_Union[navmap, _Mapping]]] = ...) -> None: ...

class navmap_req(_message.Message):
    __slots__ = ("mapname", "mapnewname")
    MAPNAME_FIELD_NUMBER: _ClassVar[int]
    MAPNEWNAME_FIELD_NUMBER: _ClassVar[int]
    mapname: str
    mapnewname: str
    def __init__(self, mapname: _Optional[str] = ..., mapnewname: _Optional[str] = ...) -> None: ...

class navmap(_message.Message):
    __slots__ = ("id", "name", "path", "metapath", "isUsed")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    METAPATH_FIELD_NUMBER: _ClassVar[int]
    ISUSED_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    path: str
    metapath: str
    isUsed: bool
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., path: _Optional[str] = ..., metapath: _Optional[str] = ..., isUsed: bool = ...) -> None: ...

class navmapdata(_message.Message):
    __slots__ = ("id", "name", "mapsize", "mapdata")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    MAPSIZE_FIELD_NUMBER: _ClassVar[int]
    MAPDATA_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    mapsize: int
    mapdata: bytes
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., mapsize: _Optional[int] = ..., mapdata: _Optional[bytes] = ...) -> None: ...

class map_file(_message.Message):
    __slots__ = ("id", "name", "yaml", "pgm_src_size", "pgm_compress")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    YAML_FIELD_NUMBER: _ClassVar[int]
    PGM_SRC_SIZE_FIELD_NUMBER: _ClassVar[int]
    PGM_COMPRESS_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    yaml: bytes
    pgm_src_size: int
    pgm_compress: bytes
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., yaml: _Optional[bytes] = ..., pgm_src_size: _Optional[int] = ..., pgm_compress: _Optional[bytes] = ...) -> None: ...

class navmapmeta(_message.Message):
    __slots__ = ("id", "name", "width", "height", "origin", "resolution")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    ORIGIN_FIELD_NUMBER: _ClassVar[int]
    RESOLUTION_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    width: int
    height: int
    origin: pos_info
    resolution: float
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., width: _Optional[int] = ..., height: _Optional[int] = ..., origin: _Optional[_Union[pos_info, _Mapping]] = ..., resolution: _Optional[float] = ...) -> None: ...

class navstatus(_message.Message):
    __slots__ = ("mode", "loopway", "isnavnext", "currentstate", "goalqueue", "priorgoalqueue", "currentqueue", "currentgoal", "sucessnum", "failednum", "intervaltime")
    MODE_FIELD_NUMBER: _ClassVar[int]
    LOOPWAY_FIELD_NUMBER: _ClassVar[int]
    ISNAVNEXT_FIELD_NUMBER: _ClassVar[int]
    CURRENTSTATE_FIELD_NUMBER: _ClassVar[int]
    GOALQUEUE_FIELD_NUMBER: _ClassVar[int]
    PRIORGOALQUEUE_FIELD_NUMBER: _ClassVar[int]
    CURRENTQUEUE_FIELD_NUMBER: _ClassVar[int]
    CURRENTGOAL_FIELD_NUMBER: _ClassVar[int]
    SUCESSNUM_FIELD_NUMBER: _ClassVar[int]
    FAILEDNUM_FIELD_NUMBER: _ClassVar[int]
    INTERVALTIME_FIELD_NUMBER: _ClassVar[int]
    mode: str
    loopway: str
    isnavnext: int
    currentstate: str
    goalqueue: str
    priorgoalqueue: str
    currentqueue: str
    currentgoal: str
    sucessnum: str
    failednum: str
    intervaltime: str
    def __init__(self, mode: _Optional[str] = ..., loopway: _Optional[str] = ..., isnavnext: _Optional[int] = ..., currentstate: _Optional[str] = ..., goalqueue: _Optional[str] = ..., priorgoalqueue: _Optional[str] = ..., currentqueue: _Optional[str] = ..., currentgoal: _Optional[str] = ..., sucessnum: _Optional[str] = ..., failednum: _Optional[str] = ..., intervaltime: _Optional[str] = ...) -> None: ...

class machineState(_message.Message):
    __slots__ = ("boottime", "updatestamp", "updatetime", "cpu", "load", "swapused", "diskroot", "port1", "port2", "port3", "port4")
    BOOTTIME_FIELD_NUMBER: _ClassVar[int]
    UPDATESTAMP_FIELD_NUMBER: _ClassVar[int]
    UPDATETIME_FIELD_NUMBER: _ClassVar[int]
    CPU_FIELD_NUMBER: _ClassVar[int]
    LOAD_FIELD_NUMBER: _ClassVar[int]
    SWAPUSED_FIELD_NUMBER: _ClassVar[int]
    DISKROOT_FIELD_NUMBER: _ClassVar[int]
    PORT1_FIELD_NUMBER: _ClassVar[int]
    PORT2_FIELD_NUMBER: _ClassVar[int]
    PORT3_FIELD_NUMBER: _ClassVar[int]
    PORT4_FIELD_NUMBER: _ClassVar[int]
    boottime: str
    updatestamp: str
    updatetime: str
    cpu: str
    load: str
    swapused: str
    diskroot: str
    port1: str
    port2: str
    port3: str
    port4: str
    def __init__(self, boottime: _Optional[str] = ..., updatestamp: _Optional[str] = ..., updatetime: _Optional[str] = ..., cpu: _Optional[str] = ..., load: _Optional[str] = ..., swapused: _Optional[str] = ..., diskroot: _Optional[str] = ..., port1: _Optional[str] = ..., port2: _Optional[str] = ..., port3: _Optional[str] = ..., port4: _Optional[str] = ...) -> None: ...

class processState(_message.Message):
    __slots__ = ("updatestamp", "updatetime", "dashgodriver", "driver", "driverimu", "pathgoimu", "flashgo", "sicktim", "gmapping", "gmappingimu", "navigation", "navigationimu", "autogmapping", "autogmappingimu", "autogmappingstart", "autonavigation", "autonavigationimu")
    UPDATESTAMP_FIELD_NUMBER: _ClassVar[int]
    UPDATETIME_FIELD_NUMBER: _ClassVar[int]
    DASHGODRIVER_FIELD_NUMBER: _ClassVar[int]
    DRIVER_FIELD_NUMBER: _ClassVar[int]
    DRIVERIMU_FIELD_NUMBER: _ClassVar[int]
    PATHGOIMU_FIELD_NUMBER: _ClassVar[int]
    FLASHGO_FIELD_NUMBER: _ClassVar[int]
    SICKTIM_FIELD_NUMBER: _ClassVar[int]
    GMAPPING_FIELD_NUMBER: _ClassVar[int]
    GMAPPINGIMU_FIELD_NUMBER: _ClassVar[int]
    NAVIGATION_FIELD_NUMBER: _ClassVar[int]
    NAVIGATIONIMU_FIELD_NUMBER: _ClassVar[int]
    AUTOGMAPPING_FIELD_NUMBER: _ClassVar[int]
    AUTOGMAPPINGIMU_FIELD_NUMBER: _ClassVar[int]
    AUTOGMAPPINGSTART_FIELD_NUMBER: _ClassVar[int]
    AUTONAVIGATION_FIELD_NUMBER: _ClassVar[int]
    AUTONAVIGATIONIMU_FIELD_NUMBER: _ClassVar[int]
    updatestamp: str
    updatetime: str
    dashgodriver: str
    driver: str
    driverimu: str
    pathgoimu: str
    flashgo: str
    sicktim: str
    gmapping: str
    gmappingimu: str
    navigation: str
    navigationimu: str
    autogmapping: str
    autogmappingimu: str
    autogmappingstart: str
    autonavigation: str
    autonavigationimu: str
    def __init__(self, updatestamp: _Optional[str] = ..., updatetime: _Optional[str] = ..., dashgodriver: _Optional[str] = ..., driver: _Optional[str] = ..., driverimu: _Optional[str] = ..., pathgoimu: _Optional[str] = ..., flashgo: _Optional[str] = ..., sicktim: _Optional[str] = ..., gmapping: _Optional[str] = ..., gmappingimu: _Optional[str] = ..., navigation: _Optional[str] = ..., navigationimu: _Optional[str] = ..., autogmapping: _Optional[str] = ..., autogmappingimu: _Optional[str] = ..., autogmappingstart: _Optional[str] = ..., autonavigation: _Optional[str] = ..., autonavigationimu: _Optional[str] = ...) -> None: ...

class lognum(_message.Message):
    __slots__ = ("logcount",)
    LOGCOUNT_FIELD_NUMBER: _ClassVar[int]
    logcount: int
    def __init__(self, logcount: _Optional[int] = ...) -> None: ...

class logdata(_message.Message):
    __slots__ = ("log",)
    LOG_FIELD_NUMBER: _ClassVar[int]
    log: str
    def __init__(self, log: _Optional[str] = ...) -> None: ...

class rp_colision_info(_message.Message):
    __slots__ = ("vid", "msg")
    VID_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    vid: str
    msg: colision_info
    def __init__(self, vid: _Optional[str] = ..., msg: _Optional[_Union[colision_info, _Mapping]] = ...) -> None: ...

class rp_ultr_info(_message.Message):
    __slots__ = ("vid", "msg")
    VID_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    vid: str
    msg: ultr_info
    def __init__(self, vid: _Optional[str] = ..., msg: _Optional[_Union[ultr_info, _Mapping]] = ...) -> None: ...

class rp_ultrasonic(_message.Message):
    __slots__ = ("vid", "msg")
    VID_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    vid: str
    msg: ultrasonic
    def __init__(self, vid: _Optional[str] = ..., msg: _Optional[_Union[ultrasonic, _Mapping]] = ...) -> None: ...

class rp_robot_info(_message.Message):
    __slots__ = ("vid", "msg")
    VID_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    vid: str
    msg: robot_info
    def __init__(self, vid: _Optional[str] = ..., msg: _Optional[_Union[robot_info, _Mapping]] = ...) -> None: ...

class rp_pos_info(_message.Message):
    __slots__ = ("vid", "msg")
    VID_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    vid: str
    msg: pos_info
    def __init__(self, vid: _Optional[str] = ..., msg: _Optional[_Union[pos_info, _Mapping]] = ...) -> None: ...

class rp_vel_info(_message.Message):
    __slots__ = ("vid", "msg")
    VID_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    vid: str
    msg: vel_info
    def __init__(self, vid: _Optional[str] = ..., msg: _Optional[_Union[vel_info, _Mapping]] = ...) -> None: ...

class rp_processState(_message.Message):
    __slots__ = ("vid", "msg")
    VID_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    vid: str
    msg: processState
    def __init__(self, vid: _Optional[str] = ..., msg: _Optional[_Union[processState, _Mapping]] = ...) -> None: ...

class rp_emergence_status(_message.Message):
    __slots__ = ("vid", "msg")
    VID_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    vid: str
    msg: emergence_status
    def __init__(self, vid: _Optional[str] = ..., msg: _Optional[_Union[emergence_status, _Mapping]] = ...) -> None: ...

class rp_machineState(_message.Message):
    __slots__ = ("vid", "msg")
    VID_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    vid: str
    msg: machineState
    def __init__(self, vid: _Optional[str] = ..., msg: _Optional[_Union[machineState, _Mapping]] = ...) -> None: ...

class rp_loc_status(_message.Message):
    __slots__ = ("vid", "msg")
    VID_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    vid: str
    msg: loc_status
    def __init__(self, vid: _Optional[str] = ..., msg: _Optional[_Union[loc_status, _Mapping]] = ...) -> None: ...

class rp_move_status(_message.Message):
    __slots__ = ("vid", "msg")
    VID_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    vid: str
    msg: move_status
    def __init__(self, vid: _Optional[str] = ..., msg: _Optional[_Union[move_status, _Mapping]] = ...) -> None: ...

class rp_charge_status(_message.Message):
    __slots__ = ("vid", "msg")
    VID_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    vid: str
    msg: charge_status
    def __init__(self, vid: _Optional[str] = ..., msg: _Optional[_Union[charge_status, _Mapping]] = ...) -> None: ...

class rp_navvoltage(_message.Message):
    __slots__ = ("vid", "msg")
    VID_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    vid: str
    msg: navvoltage
    def __init__(self, vid: _Optional[str] = ..., msg: _Optional[_Union[navvoltage, _Mapping]] = ...) -> None: ...

class rp_system_message(_message.Message):
    __slots__ = ("vid", "msg")
    VID_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    vid: str
    msg: system_message
    def __init__(self, vid: _Optional[str] = ..., msg: _Optional[_Union[system_message, _Mapping]] = ...) -> None: ...

class rp_runningmap(_message.Message):
    __slots__ = ("vid", "msg")
    VID_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    vid: str
    msg: runningmap
    def __init__(self, vid: _Optional[str] = ..., msg: _Optional[_Union[runningmap, _Mapping]] = ...) -> None: ...

class rp_runningmapupdate(_message.Message):
    __slots__ = ("vid", "msg")
    VID_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    vid: str
    msg: runningmapupdate
    def __init__(self, vid: _Optional[str] = ..., msg: _Optional[_Union[runningmapupdate, _Mapping]] = ...) -> None: ...

class rp_sensorstatus(_message.Message):
    __slots__ = ("vid", "msg")
    VID_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    vid: str
    msg: sensorstatus
    def __init__(self, vid: _Optional[str] = ..., msg: _Optional[_Union[sensorstatus, _Mapping]] = ...) -> None: ...

class rp_laserscan(_message.Message):
    __slots__ = ("vid", "msg")
    VID_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    vid: str
    msg: laserscan
    def __init__(self, vid: _Optional[str] = ..., msg: _Optional[_Union[laserscan, _Mapping]] = ...) -> None: ...

class rp_targetsocre(_message.Message):
    __slots__ = ("vid", "msg")
    VID_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    vid: str
    msg: targetsocre
    def __init__(self, vid: _Optional[str] = ..., msg: _Optional[_Union[targetsocre, _Mapping]] = ...) -> None: ...

class rp_ptz_info(_message.Message):
    __slots__ = ("vid", "msg")
    VID_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    vid: str
    msg: ptz_info
    def __init__(self, vid: _Optional[str] = ..., msg: _Optional[_Union[ptz_info, _Mapping]] = ...) -> None: ...

class rp_air_item(_message.Message):
    __slots__ = ("vid", "msg")
    VID_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    vid: str
    msg: air_item
    def __init__(self, vid: _Optional[str] = ..., msg: _Optional[_Union[air_item, _Mapping]] = ...) -> None: ...

class rp_lift_info(_message.Message):
    __slots__ = ("vid", "msg")
    VID_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    vid: str
    msg: reply_value
    def __init__(self, vid: _Optional[str] = ..., msg: _Optional[_Union[reply_value, _Mapping]] = ...) -> None: ...

class rp_trace_status(_message.Message):
    __slots__ = ("vid", "msg")
    VID_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    vid: str
    msg: trace_status
    def __init__(self, vid: _Optional[str] = ..., msg: _Optional[_Union[trace_status, _Mapping]] = ...) -> None: ...

class rp_fzulift_status(_message.Message):
    __slots__ = ("vid", "msg")
    VID_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    vid: str
    msg: reply_value
    def __init__(self, vid: _Optional[str] = ..., msg: _Optional[_Union[reply_value, _Mapping]] = ...) -> None: ...

class rp_driver_state(_message.Message):
    __slots__ = ("vid", "msg")
    VID_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    vid: str
    msg: driver_state
    def __init__(self, vid: _Optional[str] = ..., msg: _Optional[_Union[driver_state, _Mapping]] = ...) -> None: ...

class rp_obstacle_avoidance_status(_message.Message):
    __slots__ = ("vid", "msg")
    VID_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    vid: str
    msg: obstacle_avoidance_status
    def __init__(self, vid: _Optional[str] = ..., msg: _Optional[_Union[obstacle_avoidance_status, _Mapping]] = ...) -> None: ...

class robot_info(_message.Message):
    __slots__ = ("id", "ip_address", "locstatus", "navstate", "button_status", "pos", "vel", "charge_status", "voltage", "power")
    ID_FIELD_NUMBER: _ClassVar[int]
    IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    LOCSTATUS_FIELD_NUMBER: _ClassVar[int]
    NAVSTATE_FIELD_NUMBER: _ClassVar[int]
    BUTTON_STATUS_FIELD_NUMBER: _ClassVar[int]
    POS_FIELD_NUMBER: _ClassVar[int]
    VEL_FIELD_NUMBER: _ClassVar[int]
    CHARGE_STATUS_FIELD_NUMBER: _ClassVar[int]
    VOLTAGE_FIELD_NUMBER: _ClassVar[int]
    POWER_FIELD_NUMBER: _ClassVar[int]
    id: int
    ip_address: str
    locstatus: str
    navstate: str
    button_status: emergence_status
    pos: pos_info
    vel: vel_info
    charge_status: int
    voltage: float
    power: int
    def __init__(self, id: _Optional[int] = ..., ip_address: _Optional[str] = ..., locstatus: _Optional[str] = ..., navstate: _Optional[str] = ..., button_status: _Optional[_Union[emergence_status, _Mapping]] = ..., pos: _Optional[_Union[pos_info, _Mapping]] = ..., vel: _Optional[_Union[vel_info, _Mapping]] = ..., charge_status: _Optional[int] = ..., voltage: _Optional[float] = ..., power: _Optional[int] = ...) -> None: ...

class pos_info(_message.Message):
    __slots__ = ("x", "y", "yaw")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    YAW_FIELD_NUMBER: _ClassVar[int]
    x: float
    y: float
    yaw: float
    def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ..., yaw: _Optional[float] = ...) -> None: ...

class vel_info(_message.Message):
    __slots__ = ("vx", "vy", "vtheta")
    VX_FIELD_NUMBER: _ClassVar[int]
    VY_FIELD_NUMBER: _ClassVar[int]
    VTHETA_FIELD_NUMBER: _ClassVar[int]
    vx: float
    vy: float
    vtheta: float
    def __init__(self, vx: _Optional[float] = ..., vy: _Optional[float] = ..., vtheta: _Optional[float] = ...) -> None: ...

class cmd_walk(_message.Message):
    __slots__ = ("walktype", "isimu", "total", "speed", "radius")
    WALKTYPE_FIELD_NUMBER: _ClassVar[int]
    ISIMU_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    SPEED_FIELD_NUMBER: _ClassVar[int]
    RADIUS_FIELD_NUMBER: _ClassVar[int]
    walktype: int
    isimu: bool
    total: float
    speed: float
    radius: float
    def __init__(self, walktype: _Optional[int] = ..., isimu: bool = ..., total: _Optional[float] = ..., speed: _Optional[float] = ..., radius: _Optional[float] = ...) -> None: ...

class gmappingops(_message.Message):
    __slots__ = ("mapname",)
    MAPNAME_FIELD_NUMBER: _ClassVar[int]
    mapname: str
    def __init__(self, mapname: _Optional[str] = ...) -> None: ...

class navops(_message.Message):
    __slots__ = ("mapname",)
    MAPNAME_FIELD_NUMBER: _ClassVar[int]
    mapname: str
    def __init__(self, mapname: _Optional[str] = ...) -> None: ...

class traceops(_message.Message):
    __slots__ = ("mapname",)
    MAPNAME_FIELD_NUMBER: _ClassVar[int]
    mapname: str
    def __init__(self, mapname: _Optional[str] = ...) -> None: ...

class map_waypoint(_message.Message):
    __slots__ = ("mapname", "pos")
    MAPNAME_FIELD_NUMBER: _ClassVar[int]
    POS_FIELD_NUMBER: _ClassVar[int]
    mapname: str
    pos: mappos
    def __init__(self, mapname: _Optional[str] = ..., pos: _Optional[_Union[mappos, _Mapping]] = ...) -> None: ...

class mappos(_message.Message):
    __slots__ = ("posname", "posnewname", "posval")
    POSNAME_FIELD_NUMBER: _ClassVar[int]
    POSNEWNAME_FIELD_NUMBER: _ClassVar[int]
    POSVAL_FIELD_NUMBER: _ClassVar[int]
    posname: str
    posnewname: str
    posval: pos_info
    def __init__(self, posname: _Optional[str] = ..., posnewname: _Optional[str] = ..., posval: _Optional[_Union[pos_info, _Mapping]] = ...) -> None: ...

class mappos_collec(_message.Message):
    __slots__ = ("poscollec",)
    POSCOLLEC_FIELD_NUMBER: _ClassVar[int]
    poscollec: _containers.RepeatedCompositeFieldContainer[mappos]
    def __init__(self, poscollec: _Optional[_Iterable[_Union[mappos, _Mapping]]] = ...) -> None: ...

class navmode(_message.Message):
    __slots__ = ("mode",)
    MODE_FIELD_NUMBER: _ClassVar[int]
    mode: str
    def __init__(self, mode: _Optional[str] = ...) -> None: ...

class navpause(_message.Message):
    __slots__ = ("val",)
    VAL_FIELD_NUMBER: _ClassVar[int]
    val: int
    def __init__(self, val: _Optional[int] = ...) -> None: ...

class navvoltage(_message.Message):
    __slots__ = ("percentage", "voltage", "current")
    PERCENTAGE_FIELD_NUMBER: _ClassVar[int]
    VOLTAGE_FIELD_NUMBER: _ClassVar[int]
    CURRENT_FIELD_NUMBER: _ClassVar[int]
    percentage: int
    voltage: float
    current: float
    def __init__(self, percentage: _Optional[int] = ..., voltage: _Optional[float] = ..., current: _Optional[float] = ...) -> None: ...

class loc_status(_message.Message):
    __slots__ = ("value",)
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: int
    def __init__(self, value: _Optional[int] = ...) -> None: ...

class move_status(_message.Message):
    __slots__ = ("value", "posname")
    VALUE_FIELD_NUMBER: _ClassVar[int]
    POSNAME_FIELD_NUMBER: _ClassVar[int]
    value: int
    posname: str
    def __init__(self, value: _Optional[int] = ..., posname: _Optional[str] = ...) -> None: ...

class charge_handle(_message.Message):
    __slots__ = ("value",)
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: int
    def __init__(self, value: _Optional[int] = ...) -> None: ...

class charge_status(_message.Message):
    __slots__ = ("value",)
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: int
    def __init__(self, value: _Optional[int] = ...) -> None: ...

class emergence_status(_message.Message):
    __slots__ = ("value",)
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: int
    def __init__(self, value: _Optional[int] = ...) -> None: ...

class reinitpose_status(_message.Message):
    __slots__ = ("value",)
    VALUE_FIELD_NUMBER: _ClassVar[int]
    value: int
    def __init__(self, value: _Optional[int] = ...) -> None: ...

class system_message(_message.Message):
    __slots__ = ("message_type", "code", "value")
    MESSAGE_TYPE_FIELD_NUMBER: _ClassVar[int]
    CODE_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    message_type: str
    code: str
    value: str
    def __init__(self, message_type: _Optional[str] = ..., code: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

class runningmap(_message.Message):
    __slots__ = ("seq", "frameid", "resolution", "width", "height", "robotpos", "origin", "mapsize", "mapdata")
    SEQ_FIELD_NUMBER: _ClassVar[int]
    FRAMEID_FIELD_NUMBER: _ClassVar[int]
    RESOLUTION_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    ROBOTPOS_FIELD_NUMBER: _ClassVar[int]
    ORIGIN_FIELD_NUMBER: _ClassVar[int]
    MAPSIZE_FIELD_NUMBER: _ClassVar[int]
    MAPDATA_FIELD_NUMBER: _ClassVar[int]
    seq: int
    frameid: str
    resolution: float
    width: int
    height: int
    robotpos: pos_info
    origin: pos_info
    mapsize: int
    mapdata: bytes
    def __init__(self, seq: _Optional[int] = ..., frameid: _Optional[str] = ..., resolution: _Optional[float] = ..., width: _Optional[int] = ..., height: _Optional[int] = ..., robotpos: _Optional[_Union[pos_info, _Mapping]] = ..., origin: _Optional[_Union[pos_info, _Mapping]] = ..., mapsize: _Optional[int] = ..., mapdata: _Optional[bytes] = ...) -> None: ...

class runningmapupdate(_message.Message):
    __slots__ = ("seq", "frameid", "resolution", "width", "height", "robotpos", "origin", "update_size", "map_flagdata", "map_updatedata")
    SEQ_FIELD_NUMBER: _ClassVar[int]
    FRAMEID_FIELD_NUMBER: _ClassVar[int]
    RESOLUTION_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    ROBOTPOS_FIELD_NUMBER: _ClassVar[int]
    ORIGIN_FIELD_NUMBER: _ClassVar[int]
    UPDATE_SIZE_FIELD_NUMBER: _ClassVar[int]
    MAP_FLAGDATA_FIELD_NUMBER: _ClassVar[int]
    MAP_UPDATEDATA_FIELD_NUMBER: _ClassVar[int]
    seq: int
    frameid: str
    resolution: float
    width: int
    height: int
    robotpos: pos_info
    origin: pos_info
    update_size: int
    map_flagdata: _containers.RepeatedScalarFieldContainer[int]
    map_updatedata: bytes
    def __init__(self, seq: _Optional[int] = ..., frameid: _Optional[str] = ..., resolution: _Optional[float] = ..., width: _Optional[int] = ..., height: _Optional[int] = ..., robotpos: _Optional[_Union[pos_info, _Mapping]] = ..., origin: _Optional[_Union[pos_info, _Mapping]] = ..., update_size: _Optional[int] = ..., map_flagdata: _Optional[_Iterable[int]] = ..., map_updatedata: _Optional[bytes] = ...) -> None: ...

class nav_pos(_message.Message):
    __slots__ = ("name", "pos")
    NAME_FIELD_NUMBER: _ClassVar[int]
    POS_FIELD_NUMBER: _ClassVar[int]
    name: str
    pos: pos_info
    def __init__(self, name: _Optional[str] = ..., pos: _Optional[_Union[pos_info, _Mapping]] = ...) -> None: ...

class navqueue(_message.Message):
    __slots__ = ("name", "pos_queue")
    NAME_FIELD_NUMBER: _ClassVar[int]
    POS_QUEUE_FIELD_NUMBER: _ClassVar[int]
    name: str
    pos_queue: _containers.RepeatedCompositeFieldContainer[nav_pos]
    def __init__(self, name: _Optional[str] = ..., pos_queue: _Optional[_Iterable[_Union[nav_pos, _Mapping]]] = ...) -> None: ...

class navqueueinfo(_message.Message):
    __slots__ = ("queuedata",)
    QUEUEDATA_FIELD_NUMBER: _ClassVar[int]
    queuedata: _containers.RepeatedCompositeFieldContainer[navqueue]
    def __init__(self, queuedata: _Optional[_Iterable[_Union[navqueue, _Mapping]]] = ...) -> None: ...

class targetsocre(_message.Message):
    __slots__ = ("score", "type", "time")
    SCORE_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    TIME_FIELD_NUMBER: _ClassVar[int]
    score: int
    type: int
    time: int
    def __init__(self, score: _Optional[int] = ..., type: _Optional[int] = ..., time: _Optional[int] = ...) -> None: ...

class trace_cmd(_message.Message):
    __slots__ = ("cmd", "max_linear_speed", "max_angular_speed")
    CMD_FIELD_NUMBER: _ClassVar[int]
    MAX_LINEAR_SPEED_FIELD_NUMBER: _ClassVar[int]
    MAX_ANGULAR_SPEED_FIELD_NUMBER: _ClassVar[int]
    cmd: int
    max_linear_speed: float
    max_angular_speed: float
    def __init__(self, cmd: _Optional[int] = ..., max_linear_speed: _Optional[float] = ..., max_angular_speed: _Optional[float] = ...) -> None: ...

class trace_pos(_message.Message):
    __slots__ = ("id", "type", "x", "y", "yaw")
    ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    YAW_FIELD_NUMBER: _ClassVar[int]
    id: int
    type: int
    x: float
    y: float
    yaw: float
    def __init__(self, id: _Optional[int] = ..., type: _Optional[int] = ..., x: _Optional[float] = ..., y: _Optional[float] = ..., yaw: _Optional[float] = ...) -> None: ...

class trace_pos_list(_message.Message):
    __slots__ = ("pos_list",)
    POS_LIST_FIELD_NUMBER: _ClassVar[int]
    pos_list: _containers.RepeatedCompositeFieldContainer[trace_pos]
    def __init__(self, pos_list: _Optional[_Iterable[_Union[trace_pos, _Mapping]]] = ...) -> None: ...

class trace_status(_message.Message):
    __slots__ = ("status", "id_start", "id_end")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ID_START_FIELD_NUMBER: _ClassVar[int]
    ID_END_FIELD_NUMBER: _ClassVar[int]
    status: int
    id_start: int
    id_end: int
    def __init__(self, status: _Optional[int] = ..., id_start: _Optional[int] = ..., id_end: _Optional[int] = ...) -> None: ...

class joystick_cmd(_message.Message):
    __slots__ = ("cmd",)
    CMD_FIELD_NUMBER: _ClassVar[int]
    cmd: int
    def __init__(self, cmd: _Optional[int] = ...) -> None: ...

class sonar_distance(_message.Message):
    __slots__ = ("sonar_obstacle", "sonar_release")
    SONAR_OBSTACLE_FIELD_NUMBER: _ClassVar[int]
    SONAR_RELEASE_FIELD_NUMBER: _ClassVar[int]
    sonar_obstacle: int
    sonar_release: int
    def __init__(self, sonar_obstacle: _Optional[int] = ..., sonar_release: _Optional[int] = ...) -> None: ...

class sonar_distances(_message.Message):
    __slots__ = ("sonar",)
    SONAR_FIELD_NUMBER: _ClassVar[int]
    sonar: _containers.RepeatedCompositeFieldContainer[sonar_distance]
    def __init__(self, sonar: _Optional[_Iterable[_Union[sonar_distance, _Mapping]]] = ...) -> None: ...

class sonar_data(_message.Message):
    __slots__ = ("data",)
    DATA_FIELD_NUMBER: _ClassVar[int]
    data: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, data: _Optional[_Iterable[int]] = ...) -> None: ...

class sensor_condition(_message.Message):
    __slots__ = ("imu", "sonar", "fall", "anti_collision", "infrared", "lidar")
    IMU_FIELD_NUMBER: _ClassVar[int]
    SONAR_FIELD_NUMBER: _ClassVar[int]
    FALL_FIELD_NUMBER: _ClassVar[int]
    ANTI_COLLISION_FIELD_NUMBER: _ClassVar[int]
    INFRARED_FIELD_NUMBER: _ClassVar[int]
    LIDAR_FIELD_NUMBER: _ClassVar[int]
    imu: _containers.RepeatedScalarFieldContainer[int]
    sonar: _containers.RepeatedScalarFieldContainer[int]
    fall: _containers.RepeatedScalarFieldContainer[int]
    anti_collision: _containers.RepeatedScalarFieldContainer[int]
    infrared: _containers.RepeatedScalarFieldContainer[int]
    lidar: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, imu: _Optional[_Iterable[int]] = ..., sonar: _Optional[_Iterable[int]] = ..., fall: _Optional[_Iterable[int]] = ..., anti_collision: _Optional[_Iterable[int]] = ..., infrared: _Optional[_Iterable[int]] = ..., lidar: _Optional[_Iterable[int]] = ...) -> None: ...

class targetcommand(_message.Message):
    __slots__ = ("commandtype", "time")
    COMMANDTYPE_FIELD_NUMBER: _ClassVar[int]
    TIME_FIELD_NUMBER: _ClassVar[int]
    commandtype: int
    time: int
    def __init__(self, commandtype: _Optional[int] = ..., time: _Optional[int] = ...) -> None: ...

class targetmode(_message.Message):
    __slots__ = ("targettype", "limitmode")
    TARGETTYPE_FIELD_NUMBER: _ClassVar[int]
    LIMITMODE_FIELD_NUMBER: _ClassVar[int]
    targettype: int
    limitmode: int
    def __init__(self, targettype: _Optional[int] = ..., limitmode: _Optional[int] = ...) -> None: ...

class sensorstatus(_message.Message):
    __slots__ = ("laser", "odometry", "falling_resistant", "sonar")
    LASER_FIELD_NUMBER: _ClassVar[int]
    ODOMETRY_FIELD_NUMBER: _ClassVar[int]
    FALLING_RESISTANT_FIELD_NUMBER: _ClassVar[int]
    SONAR_FIELD_NUMBER: _ClassVar[int]
    laser: int
    odometry: int
    falling_resistant: _containers.RepeatedScalarFieldContainer[int]
    sonar: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, laser: _Optional[int] = ..., odometry: _Optional[int] = ..., falling_resistant: _Optional[_Iterable[int]] = ..., sonar: _Optional[_Iterable[int]] = ...) -> None: ...

class laserscan(_message.Message):
    __slots__ = ("angle_min", "angle_max", "angle_increment", "range_min", "range_max", "ranges", "intensities")
    ANGLE_MIN_FIELD_NUMBER: _ClassVar[int]
    ANGLE_MAX_FIELD_NUMBER: _ClassVar[int]
    ANGLE_INCREMENT_FIELD_NUMBER: _ClassVar[int]
    RANGE_MIN_FIELD_NUMBER: _ClassVar[int]
    RANGE_MAX_FIELD_NUMBER: _ClassVar[int]
    RANGES_FIELD_NUMBER: _ClassVar[int]
    INTENSITIES_FIELD_NUMBER: _ClassVar[int]
    angle_min: float
    angle_max: float
    angle_increment: float
    range_min: float
    range_max: float
    ranges: _containers.RepeatedScalarFieldContainer[float]
    intensities: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, angle_min: _Optional[float] = ..., angle_max: _Optional[float] = ..., angle_increment: _Optional[float] = ..., range_min: _Optional[float] = ..., range_max: _Optional[float] = ..., ranges: _Optional[_Iterable[float]] = ..., intensities: _Optional[_Iterable[float]] = ...) -> None: ...

class ptz_info(_message.Message):
    __slots__ = ("command", "value")
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    command: int
    value: int
    def __init__(self, command: _Optional[int] = ..., value: _Optional[int] = ...) -> None: ...

class air_item(_message.Message):
    __slots__ = ("pm2dot5", "tvoc", "smog", "temperature", "humidity", "ch2o", "ch4", "pm10")
    PM2DOT5_FIELD_NUMBER: _ClassVar[int]
    TVOC_FIELD_NUMBER: _ClassVar[int]
    SMOG_FIELD_NUMBER: _ClassVar[int]
    TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    HUMIDITY_FIELD_NUMBER: _ClassVar[int]
    CH2O_FIELD_NUMBER: _ClassVar[int]
    CH4_FIELD_NUMBER: _ClassVar[int]
    PM10_FIELD_NUMBER: _ClassVar[int]
    pm2dot5: float
    tvoc: float
    smog: float
    temperature: float
    humidity: float
    ch2o: float
    ch4: float
    pm10: float
    def __init__(self, pm2dot5: _Optional[float] = ..., tvoc: _Optional[float] = ..., smog: _Optional[float] = ..., temperature: _Optional[float] = ..., humidity: _Optional[float] = ..., ch2o: _Optional[float] = ..., ch4: _Optional[float] = ..., pm10: _Optional[float] = ...) -> None: ...

class Person(_message.Message):
    __slots__ = ("flag", "stateFlag", "imgFlag")
    FLAG_FIELD_NUMBER: _ClassVar[int]
    STATEFLAG_FIELD_NUMBER: _ClassVar[int]
    IMGFLAG_FIELD_NUMBER: _ClassVar[int]
    flag: int
    stateFlag: int
    imgFlag: int
    def __init__(self, flag: _Optional[int] = ..., stateFlag: _Optional[int] = ..., imgFlag: _Optional[int] = ...) -> None: ...

class Response(_message.Message):
    __slots__ = ("message", "faceFlag", "img", "Width", "Height")
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    FACEFLAG_FIELD_NUMBER: _ClassVar[int]
    IMG_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    message: str
    faceFlag: int
    img: bytes
    Width: int
    Height: int
    def __init__(self, message: _Optional[str] = ..., faceFlag: _Optional[int] = ..., img: _Optional[bytes] = ..., Width: _Optional[int] = ..., Height: _Optional[int] = ...) -> None: ...

class moving_param_default(_message.Message):
    __slots__ = ("map", "init_pose")
    MAP_FIELD_NUMBER: _ClassVar[int]
    INIT_POSE_FIELD_NUMBER: _ClassVar[int]
    map: str
    init_pose: pos_info
    def __init__(self, map: _Optional[str] = ..., init_pose: _Optional[_Union[pos_info, _Mapping]] = ...) -> None: ...

class buzzer_info(_message.Message):
    __slots__ = ("frequency", "status")
    FREQUENCY_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    frequency: int
    status: int
    def __init__(self, frequency: _Optional[int] = ..., status: _Optional[int] = ...) -> None: ...

class colision_info(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, status: _Optional[_Iterable[int]] = ...) -> None: ...

class ultrasonic(_message.Message):
    __slots__ = ("distance",)
    DISTANCE_FIELD_NUMBER: _ClassVar[int]
    distance: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, distance: _Optional[_Iterable[int]] = ...) -> None: ...

class ultr_info(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: int
    def __init__(self, status: _Optional[int] = ...) -> None: ...

class ultr_cmd(_message.Message):
    __slots__ = ("cmd", "alarm_distance", "reset_alarm_dis")
    CMD_FIELD_NUMBER: _ClassVar[int]
    ALARM_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    RESET_ALARM_DIS_FIELD_NUMBER: _ClassVar[int]
    cmd: int
    alarm_distance: int
    reset_alarm_dis: int
    def __init__(self, cmd: _Optional[int] = ..., alarm_distance: _Optional[int] = ..., reset_alarm_dis: _Optional[int] = ...) -> None: ...

class driver_state_cmd(_message.Message):
    __slots__ = ("cmd",)
    CMD_FIELD_NUMBER: _ClassVar[int]
    cmd: int
    def __init__(self, cmd: _Optional[int] = ...) -> None: ...

class driver_state(_message.Message):
    __slots__ = ("left_driver_connection_status", "left_driver_lock_status", "left_driver_error_info", "left_driver_current", "left_driver_limit_voltage", "left_driver_encoder", "left_driver_sq1", "right_driver_connection_status", "right_driver_lock_status", "right_driver_error_info", "right_driver_current", "right_driver_limit_voltage", "right_driver_encoder", "right_driver_sq1", "driver_reserved")
    LEFT_DRIVER_CONNECTION_STATUS_FIELD_NUMBER: _ClassVar[int]
    LEFT_DRIVER_LOCK_STATUS_FIELD_NUMBER: _ClassVar[int]
    LEFT_DRIVER_ERROR_INFO_FIELD_NUMBER: _ClassVar[int]
    LEFT_DRIVER_CURRENT_FIELD_NUMBER: _ClassVar[int]
    LEFT_DRIVER_LIMIT_VOLTAGE_FIELD_NUMBER: _ClassVar[int]
    LEFT_DRIVER_ENCODER_FIELD_NUMBER: _ClassVar[int]
    LEFT_DRIVER_SQ1_FIELD_NUMBER: _ClassVar[int]
    RIGHT_DRIVER_CONNECTION_STATUS_FIELD_NUMBER: _ClassVar[int]
    RIGHT_DRIVER_LOCK_STATUS_FIELD_NUMBER: _ClassVar[int]
    RIGHT_DRIVER_ERROR_INFO_FIELD_NUMBER: _ClassVar[int]
    RIGHT_DRIVER_CURRENT_FIELD_NUMBER: _ClassVar[int]
    RIGHT_DRIVER_LIMIT_VOLTAGE_FIELD_NUMBER: _ClassVar[int]
    RIGHT_DRIVER_ENCODER_FIELD_NUMBER: _ClassVar[int]
    RIGHT_DRIVER_SQ1_FIELD_NUMBER: _ClassVar[int]
    DRIVER_RESERVED_FIELD_NUMBER: _ClassVar[int]
    left_driver_connection_status: int
    left_driver_lock_status: int
    left_driver_error_info: int
    left_driver_current: float
    left_driver_limit_voltage: float
    left_driver_encoder: int
    left_driver_sq1: int
    right_driver_connection_status: int
    right_driver_lock_status: int
    right_driver_error_info: int
    right_driver_current: float
    right_driver_limit_voltage: float
    right_driver_encoder: int
    right_driver_sq1: int
    driver_reserved: int
    def __init__(self, left_driver_connection_status: _Optional[int] = ..., left_driver_lock_status: _Optional[int] = ..., left_driver_error_info: _Optional[int] = ..., left_driver_current: _Optional[float] = ..., left_driver_limit_voltage: _Optional[float] = ..., left_driver_encoder: _Optional[int] = ..., left_driver_sq1: _Optional[int] = ..., right_driver_connection_status: _Optional[int] = ..., right_driver_lock_status: _Optional[int] = ..., right_driver_error_info: _Optional[int] = ..., right_driver_current: _Optional[float] = ..., right_driver_limit_voltage: _Optional[float] = ..., right_driver_encoder: _Optional[int] = ..., right_driver_sq1: _Optional[int] = ..., driver_reserved: _Optional[int] = ...) -> None: ...

class obstacle_avoidance_cmd(_message.Message):
    __slots__ = ("cmd",)
    CMD_FIELD_NUMBER: _ClassVar[int]
    cmd: int
    def __init__(self, cmd: _Optional[int] = ...) -> None: ...

class obstacle_avoidance_status(_message.Message):
    __slots__ = ("sonar", "anti_collision", "drop_proof", "infrared", "lidar")
    SONAR_FIELD_NUMBER: _ClassVar[int]
    ANTI_COLLISION_FIELD_NUMBER: _ClassVar[int]
    DROP_PROOF_FIELD_NUMBER: _ClassVar[int]
    INFRARED_FIELD_NUMBER: _ClassVar[int]
    LIDAR_FIELD_NUMBER: _ClassVar[int]
    sonar: int
    anti_collision: int
    drop_proof: int
    infrared: int
    lidar: int
    def __init__(self, sonar: _Optional[int] = ..., anti_collision: _Optional[int] = ..., drop_proof: _Optional[int] = ..., infrared: _Optional[int] = ..., lidar: _Optional[int] = ...) -> None: ...

class inplace_info(_message.Message):
    __slots__ = ("angle",)
    ANGLE_FIELD_NUMBER: _ClassVar[int]
    angle: float
    def __init__(self, angle: _Optional[float] = ...) -> None: ...
