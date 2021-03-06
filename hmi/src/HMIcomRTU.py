#   -- Función principal -- . Interactúa con el resto del software HMI.
##
#
# @file HMIcomRTU.py
#
# @brief Esta función recibe la llamada desde el software HMI principal
# cada vez que necesita enviar u obtener datos de la unidad remota RTU.
# El ciclo de intercambio de tramas se realiza a demanda del cliente, en este caso el 
# software HMI mediante el presente módulo.
# 
# @param a_HMIDataByte Variable tipo array que recibe los datos tipo -int, float- para 
# enviar a RTU.
# @param a_HMIDataString Variable tipo array que recibe los datos tipo -String- para 
# enviar a RTU.
# @param b_connect Variable tipo boleana que indica el estado de la conexión con la RTU
# 0: Desconexión
# 1: Conexión
# @param s_sock Variable tipo <socket> que almacena la identidad del socket 
# generado en la conexión establecida con la RTU.
# @param s_ip Variable tipo string que recibe la dirección s_ip que se ingresó para la RTU.
# @param s_port Variable tipo string que recibe el puerto que se ingresó para la RTU.
#  
# @return a_RTUData Variable tipo array que retorna los datos recibidos desde la RTU.
# @return b_connect 
# @return s_sock
##


import socket
import sys
import time
from depurador import *


    #   -- Constantes --
s_CLIENT_ID = "SM13;" 
# Convertir en dato de entrada. IMPORTANTE: DEBEN DEMANDARSE CUATRO CARACTERES. Es para mantener fromato de trama
f_MAX_GRADOS = 359.999
i_MAX_CUENTAS = int(0xFFFF)
i_BUFFER_RCV = 100    # Tamaño del buffer de recepción. 
                    # Los datos se emiten desde RTU, utilizando el carácter '/00' en el sobrante del tamaño del buffer respecto al de los datos en la  trama.
   
##
# @file HMIcomRTU.py
#

# @Brief Este módulo se encarga de administrar la comunicación vía ethernet que se 
# @brief Este módulo se encarga de administrar la comunicación vía ethernet que se 
# lleva a cabo entre el software HMI y la Unidad Terminal Remota -RTU- (dentro del Fixture 
# Controller -FC-) que comanda el Fixture Harness -FH-. 
##



def enviar_a_y_recibir_de_rtu(a_HMIDataByte, a_HMIDataString, b_connect, s_sock, s_ip, s_port):

        # Acondicionamiento de datos a enviar.
    a_HMIDataString, a_HMIDataByte = HMITranslate(a_HMIDataString, a_HMIDataByte)

        # Si no hay conexión, debe conectar/re-conectar      
    if b_connect == 0:
        s_sock, b_connect = RTU_connect(b_connect, s_ip, s_port)

        # Transmisión de tramas y recepción de datos desde RTU -a_RTUData-.
    a_RTUData, b_connect, s_sock = DataTxRx(a_HMIDataByte, a_HMIDataString, s_CLIENT_ID, s_sock, b_connect)

    depurador(2, "HMIcomRTU", "****************************************")
    depurador(2, "HMIcomRTU", "- Enviando...")
    depurador(2, "HMIcomRTU", "- Tx--> HMIDataByte: " + str(a_HMIDataByte))
    depurador(2, "HMIcomRTU", "- Tx--> HMIDataString: " + str(a_HMIDataString))
    depurador(2, "HMIcomRTU", " ")
        
    # Valores de salida para módulo HMIcomRTU
    return a_RTUData, b_connect, s_sock
    



# @brief Esta función implementa la creación y posterior conexión del socket con la RTU. 
# Se establece el tiempo de respuesta máximo -time out- para establecer conexión, los 
# tamaños de buffer para recepción/emisión, y tipo de socket. 
# 
# @param b_connect Variable tipo boleana que indica el estado de la conexión con la RTU
# 0: Desconexión
# 1: Conexión
# @param s_sock Variable tipo <socket> que almacena la identidad del socket generado en la 
# conexión establecida con la RTU
# @param s_ip Variable tipo string que recibe la dirección s_ip que se ingresó para la RTU
# @param s_port Variable tipo string que recibe el puerto que se ingresó para la RTU
#  
# @return b_connect 
# @return s_sock
##
#   -- Creación y conexión de Socket --
def RTU_connect(b_connect, s_ip, s_port):

    try:
        s_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as err:
        depurador(2, "HMIcomRTU", "****************************************")
        depurador(2, "HMIcomRTU", "Error al crear el socket")
        depurador(2, "HMIcomRTU", "Razon: %s" %str(err))
        depurador(2, "HMI", " ")
    else:
        server_address = (s_ip, s_port)
        s_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 200)
        s_sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 200)
        s_sock.settimeout(10)
        try:
            s_sock.connect(server_address)
        except socket.error as err:
            b_connect = False
            depurador(2, "HMIcomRTU", "****************************************")
            depurador(2, "HMIcomRTU", "No se encuentra disponible la RTU con IP: %s, en el puerto %s" %(s_ip, s_port))
            depurador(2, "HMI", " ")
        except:
            print("aca")
        else:
            b_connect = True
    finally:
        return s_sock, b_connect

##
# @brief Esta función se encarga de la emisión y recepción de las tramas ethernet con la RTU.
# 
# @param a_HMIDataByte Variable tipo array que recibe los datos tipo -int, float- para 
# enviar a RTU.
# @param a_HMIDataString Variable tipo array que recibe los datos tipo -String- para 
# enviar a RTU.
# @param s_CLIENT_ID Variable tipo string que se utiliza para verificar identidad del lado RTU.
# @param s_sock Variable tipo <socket> que almacena la identidad del socket 
# generado en la conexión establecida con la RTU.
# @param b_connect Variable tipo boleana que indica el estado de la conexión con la RTU
# 0: Desconexión
# 1: Conexión
#  
# @return a_RTUDataTx Variable tipo array que retorna los datos recibidos desde la RTU.
# @return b_connect 
# @return s_sock
##
 #   -- Transmisión de los datos HMI hacia RTU, y Recepción de los datos RTU en trama de respuesta. 
def DataTxRx(a_HMIDataByte, a_HMIDataString, s_CLIENT_ID, s_sock, b_connect):
        
    a_RTUDataRx = 0

    a_HMIDataString += s_CLIENT_ID

    # Define tiempo de espera 500 mseg para envío y recepción de tramas.
    s_sock.settimeout(10)
   
    # Realiza el envío de la trama compuesta por los dos tipos de datos -int- y -string- convirtiendolos al tipo -byte-.
    try:
        s_sock.send(bytes(a_HMIDataByte) + a_HMIDataString.encode())
    except socket.error as err:
        b_connect = False # Se desconectó, o la conexión tiene latencia, dando lugar a TimeOut
        depurador(2, "HMIcomRTU", "****************************************")
        depurador(2, "HMIcomRTU", "Razón: %s" %str(err))
        depurador(2, "HMI", " ")
    else: 
        # Recepción de datos desde RTU. Desentrama y devuelve los datos de red traducidos al formato HMI.
        try:    
            a_RTUDataRx = s_sock.recv(i_BUFFER_RCV)
        except socket.error as err: # Al producirse desconexión, no retorna los datos, y b_connect=0
            b_connect = False
            depurador(2, "HMIcomRTU", "****************************************")
            depurador(2, "HMIcomRTU", "\n No se recibió trama de la RTU")
            depurador(2, "HMIcomRTU", "Razon: %s" %str(err))
            depurador(2, "HMI", " ")
        else:
            try: 
                a_RTUDataRx, b_connect = RTUTranslate(a_RTUDataRx)
            except socket.error as err: # Al producirse desconexión, no retorna los datos, y b_connect=False
                b_connect = False
                depurador(2, "HMIcomRTU", "****************************************")
                depurador(2, "HMIcomRTU", "Se produjo desconexión de la RTU")
                depurador(2, "HMIcomRTU", "Se produjo desconexión -a_RTUDataRx, Razon: %s" %str(err))
                depurador(2, "HMI", " ")
        finally:
            return a_RTUDataRx, b_connect, s_sock # HMI
   

##
# @brief Esta función se encarga de la transducción de los comandos HMI -tipo string- a valores 
# de red, que conformarán la trama ethernet
#
# @param a_HMIDataByte Variable tipo array que recibe los datos tipo -int, float- para 
# enviar a RTU.
# @param a_HMIDataString Variable tipo array que recibe los datos tipo -String- para 
# enviar a RTU.
#  
# @return a_HMIDataByte Retorna valores tipo -Int, Float- converidos a valores de red tipo -Byte-
# @return a_HMIDataString Retorna valores tipo -String- converidos a valores de red tipo -Byte-
##
#   -- Transducción de los valores HMI tipo -Char-, para constituír la trama a enviar por ethernet.
def HMITranslate(a_HMIDataString, a_HMIDataByte):
    
    #   -- a_HMIDataString --.
    # Transducción de los comandos HMI -tipo string- a valores de red, que conformarán la trama ethernet.
    s_mode, s_freeRunAxis, s_freeRunDir, s_ctrlEn, s_stallEn, s_liftDir = a_HMIDataString
    #   -- s_mode --
    if s_mode == "STOP":
        s_mode = "STOP;"
    elif s_mode == "FREE_RUN":
        s_mode = "FRUN;"
    elif s_mode == "AUTOMATIC":
        s_mode = "AUTO;"
    elif s_mode == "LIFT":
        s_mode = "LIFT;"
    else:  
        depurador(2, "HMI", "****************************************")
        depurador(2, "HMIcomRTU","error -s_mode-")
        depurador(2, "HMI", " ")
     #   -- s_freeRunAxis --
    if s_freeRunAxis == "ARM":
        s_freeRunAxis = "ARM_;"
    elif s_freeRunAxis == "POLE":
        s_freeRunAxis = "POLE;"
    else:  
        depurador(2, "HMI", "****************************************")
        depurador(2, "HMIcomRTU","error -s_freeRunAxis-")
        depurador(2, "HMI", " ")
     #   -- s_freeRunDir --
    if s_freeRunDir == "DIR_CW":
        s_freeRunDir = "CW__;"
    elif s_freeRunDir == "CCW_DIR":
        s_freeRunDir = "CCW_;"
    else:  
        depurador(2, "HMI", "****************************************")
        depurador(2, "HMIcomRTU","error -s_freeRunDir-")
        depurador(2, "HMI", " ")
    #   -- s_ctrlEn --
    if s_ctrlEn == "CONTROL_ENABLE":
        s_ctrlEn = "CTLE;"
    elif s_ctrlEn == "DISABLE_CONTROL":
        s_ctrlEn = "DCTL;"
    else:  
        depurador(2, "HMI", "****************************************")
        depurador(2, "HMIcomRTU","error -s_ctrlEn-")
        depurador(2, "HMI", " ")
        #   -- s_stallEn --
    if s_stallEn == "STALL_ENABLE":
        s_stallEn = "STLE;"
    elif s_stallEn == "DISABLE_STALL":
        s_stallEn = "DSTL;"
    else:  
        depurador(2, "HMI", "****************************************")
        depurador(2, "HMIcomRTU","error -s_stallEn-")
        depurador(2, "HMI", " ")
        #   -- s_liftDir --
    if s_liftDir == "LIFT_UP":
        s_liftDir = "LFUP;"
    elif s_liftDir == "LIFT_DOWN":
        s_liftDir = "LFDW;"
    else:  
        depurador(2, "HMI", "****************************************")
        depurador(2, "HMIcomRTU","error -lifDir-")
        depurador(2, "HMI", " ")
    try:
        a_HMIDataString = s_mode + s_freeRunAxis + s_freeRunDir + s_ctrlEn + s_stallEn + s_liftDir
    except:
         depurador(2, "HMI", "****************************************")
         depurador(2, "HMIcomRTU","error - HMITranslate: a_HMIDataString")
         depurador(2, "HMI", " ")

    #   -- a_HMIDataByte --.
    # Transducción de los comandos HMI a valores de red, que conformarán la trama ethernet.
    f_posCmdArm, f_posCmdPole, ui_velCmdArm, ui_velCmdPole = a_HMIDataByte 
        # Conversión de tipo para ángulos ARM y Pole. -float- a -uint16-
    ui_posCmdArm_LSB, ui_posCmdArm_MSB = LSB_MSB(f_posCmdArm)
    ui_posCmdPole_LSB, ui_posCmdPole_MSB = LSB_MSB(f_posCmdPole)
    a_HMIDataByte = ui_posCmdArm_LSB, ui_posCmdArm_MSB, ui_posCmdPole_LSB, ui_posCmdPole_MSB, ui_velCmdArm, ui_velCmdPole

        # Retorna las variables traducidas para ser enviadas por ETH -Variables de red-
    return a_HMIDataString, a_HMIDataByte

##
# @brief Esta función se encarga del desentramado, y posterior transducción de los valores 
# recibidos por trama Ethernet desde la RTU.
#
# @param a_RTUDataRx Variable tipo array que almacena los datos tipo -Byte- recibidos mediante 
# la trama que envió la RTU.
#
# @return a_RTUData Variable tipo array que retorna los datos recibidos desde la RTU. 
# @return b_connect Variable tipo boleana que indica el estado de la conexión con la RTU.
# 0: Desconexión
# 1: Conexión
# 
##
#   -- Desentramado, y transducción de los valores recibidos por trama Ethernet desde RTU.
def RTUTranslate(a_RTUDataRx):
    b_connect = True
    # Destramado
    # Se juntan los datos numéricos de resolver y velocidad en una lista-.
    a_RTUDataByte = list(a_RTUDataRx[0:6])
    # Se convierten los datos de -Byte- a -String- mediante -decode()-.
    a_RTUDataString = a_RTUDataRx[6:].decode()

    depurador(2, "HMIcomRTU", "****************************************")
    depurador(2, "HMIcomRTU", "- Recibiendo...")
    depurador(3, "HMIcomRTU","- Rx<-- RTUDataByte   :" + str(a_RTUDataByte))
    depurador(3, "HMIcomRTU","- Rx<-- RTUDataString :" + str(a_RTUDataString))
    
        # Conversión del resultado de resolver a ángulos. -Byte- a -Float-
    #if(True):
    try:   
        # Conversión: -uint16- a -float- para angulo y velocidades recibidos de los resolvers.
        #   -- posAct --
        f_posActArm_MSB = int(a_RTUDataByte[0]) #/i_MAX_CUENTAS)*f_MAX_GRADOS
        f_posActArm_LSB = int(a_RTUDataByte[1]) #/i_MAX_CUENTAS)*f_MAX_GRADOS
        f_posActArm = f_posActArm_MSB*255 + f_posActArm_LSB

        f_posActPole_MSB = int(a_RTUDataByte[2]) #/i_MAX_CUENTAS)*f_MAX_GRADOS
        f_posActPole_LSB = int(a_RTUDataByte[3]) #/i_MAX_CUENTAS)*f_MAX_GRADOS
        f_posActPole = f_posActPole_MSB*255 + f_posActPole_LSB
        #   -- velAct --
        f_velActArm = int(a_RTUDataByte[4])
        f_velActPole = int(a_RTUDataByte[5])
        
        b_cwLimitArm, b_ccwLimitArm, b_cwLimitPole, b_ccwLimitPole, b_limitDown, b_limitUp, b_stallAlm, status = a_RTUDataString.split(";")

        # Conversion de comandos. -Char- a -Bool-.
        if b_cwLimitArm  == "ACW_RUN":
            b_cwLimitArm = False
        elif b_cwLimitArm  == "ACW_LIM":
            b_cwLimitArm = True
        else: 
            depurador(2, "HMI", "****************************************")
            depurador(2, "HMIcomRTU","error -b_cwLimitArm- RTUTranslate")
            depurador(2, "HMI", " ")
            # Conversion de comandos. -Char- a -Bool-.
            # b_ccwLimitArm
        if b_ccwLimitArm  == "ACC_RUN":
            b_ccwLimitArm = False
        elif b_ccwLimitArm  == "ACC_LIM":
            b_ccwLimitArm = True
        else: 
             depurador(2, "HMI", "****************************************")
             depurador(2, "HMIcomRTU","error -b_ccwLimitArm- RTUTranslate")
             depurador(2, "HMI", " ")
            # Conversion de comandos. -Char- a -Bool-.
            # b_cwLimitPole
        if b_cwLimitPole  == "PCW_RUN":
            b_cwLimitPole = False
        elif b_cwLimitPole  == "PCW_LIM":
            b_cwLimitPole = True
        else: 
             depurador(2, "HMI", "****************************************")
             depurador(2, "HMIcomRTU","error -b_cwLimitPole- RTUTranslate")
             depurador(2, "HMI", " ")
            # Conversion de comandos. -Char- a -Bool-.
            # b_ccwLimitPole
        if b_ccwLimitPole  == "PCC_RUN":
            b_ccwLimitPole = False
        elif b_ccwLimitPole  == "PCC_LIM":
            b_ccwLimitPole = True
        else: 
             depurador(2, "HMI", "****************************************")
             depurador(2, "HMIcomRTU","error -b_ccwLimitPole- RTUTranslate")
             depurador(2, "HMI", " ")
        # Conversion de comandos. -Char- a -Bool-.
        # b_limitUp
        if b_limitUp  == "LUP_RUN":
            b_limitUp = False
        elif b_limitUp  == "LUP_LIM":
            b_limitUp = True
        else: 
             depurador(2, "HMI", "****************************************")
             depurador(2, "HMIcomRTU","error -b_limitUp- RTUTranslate")
             depurador(2, "HMI", " ")
        # Conversion de comandos. -Char- a -Bool-.
        # b_limitDown
        if b_limitDown  == "LDW_RUN":
            b_limitDown = False
        elif b_limitDown  == "LDW_LIM":
            b_limitDown = True
        else: 
             depurador(2, "HMI", "****************************************")
             depurador(2, "HMIcomRTU","error -b_limitDown- RTUTranslate")
             depurador(2, "HMI", " ")
            # Conversion de comandos. -Char- a -Bool-.
            # b_stallAlm
        if b_stallAlm  == "STL_RUN":
            b_stallAlm = False
        elif b_stallAlm  == "STL_ALM":
            b_stallAlm = True
        else: 
             depurador(2, "HMI", "****************************************")
             depurador(2, "HMIcomRTU","error -b_stallAlm- RTUTranslate")
             depurador(2, "HMI", " ")
            # Manejo de errores de conexión 
        if status == "81":
            depurador(2, "HMI", "****************************************")
            depurador(2, "HMIcomRTU","- ClientId incorrecto - Desconectando RTU.")
            depurador(2, "HMI", " ")
            b_connect = False
        elif status == "42":
            depurador(2, "HMIcomRTU","- Se recibió trama vacía")
        elif status == "43":
            depurador(2, "HMI", "****************************************")
            depurador(2, "HMIcomRTU","- No se pudo enviar trama desde RTU.")
            depurador(2, "HMI", " ")
        
        a_RTUDataOutput = [f_posActArm, f_posActPole, f_velActArm, f_velActPole, b_cwLimitArm, b_ccwLimitArm, b_cwLimitPole, b_ccwLimitPole, b_limitUp, b_limitDown, b_stallAlm]
        #depurador(3, "HMIcomRTU","- output :" + str(a_RTUDataOutput))

    except Exception as err:
        depurador(4, "HMIcomRTU", "****************************************")
        depurador(4, "HMIcomRTU","- Error en formato de trama:" + str(err))
        depurador(4, "HMIcomRTU", " ")
        # status 
        sys.exit()
            
    finally:
        depurador(4, "HMIcomRTU","- Finalizando RTUTranslate()")
        depurador(4, "HMIcomRTU","- Output: " + str(a_RTUDataOutput))
        return a_RTUDataOutput, b_connect # DataTxRx

##
# @brief Esta función se encarga de la conversíon para los valores de angulos expresados en grados 
# tipo -Float- a valores de resolver para ser enviados en la trama hacia la RTU. 
# 
#
# @param ui_grd Variable tipo -uint- que convierte los valores de resolver recibidos en la trama a
#  valores de angulos expresados en grados -Float-.
#
# @return ui_grd_LSB Variable tipo -uint- que retorna el byte menos significativo a ser enviado en
# trama hacia RTU. 
# @return ui_grd_MSB Variable tipo -uint- que retorna el byte más significativo a ser enviado en
# trama hacia RTU. 
# 
##
def LSB_MSB(ui_grd):
    depurador(4, "HMIcomRTU", "****************************************")
    #ui_grd = ui_grd/f_MAX_GRADOS
    #ui_grd *= i_MAX_CUENTAS
    ui_grd = int(ui_grd)
    depurador(4, "HMIcomRTU","- Separando en 2 bytes: " + str(ui_grd))
    ui_grd_MSB = int(ui_grd/256)
    ui_grd_LSB = ui_grd - (256*ui_grd_MSB)
    depurador(4, "HMIcomRTU","- Byte MSB: " + str(ui_grd_MSB))
    depurador(4, "HMIcomRTU","- Byte LSB: " + str(ui_grd_LSB))
    depurador(4, "HMIcomRTU", " ")
    return ui_grd_LSB, ui_grd_MSB
    

