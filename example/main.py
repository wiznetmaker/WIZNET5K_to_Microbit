import network
from machine import Pin,SPI,UART
from microbit_to_wiznet5k import Microbit_to_wiznet5k, Microbit_to_wiznet5k_Mqtt

def main():
    uart=UART(1, baudrate=115200, tx=Pin(4), rx=Pin(5))
    spi=SPI(0,2_000_000, mosi=Pin(19),miso=Pin(16),sck=Pin(18))
    nic = network.WIZNET5K(spi,Pin(17),Pin(20)) #spi,cs,reset pin
    nic.active(True)
    nic.ifconfig('dhcp')
    print('IP address :', nic.ifconfig())
    
    mb_process = Microbit_to_wiznet5k(uart)
    

    while(1):
        mb_process.check_uart_form_microbit()
        

if __name__ == "__main__":
    main()