import sys
import os
import enum
import socket
import struct



blockSize = 512
modeOctet = "octet"
port = 69
timeOut = 3


class TftpProcessor(object):

    class TftpPacketType(enum.Enum):

        RRQ = 1
        WRQ = 2
        DATA = 3
        ACK = 4
        ERROR = 5

    def __init__(self):

        self.packet_buffer = []
        self.fileName = None
        pass

    def _empty_filename_used(self):

        self.fileName = None


    def upload_file(self, file_path_on_server):

        write_request = bytearray()
        write_request.append(0)
        write_request.append(2)
        filename = bytearray(file_path_on_server.encode('utf-8'))
        write_request += filename
        write_request.append(0)
        mode = bytearray(bytes(modeOctet, 'utf-8'))
        write_request += mode
        write_request.append(0)
        self.packet_buffer.append(write_request)

        self.fileName = open(file_path_on_server, 'rb')



    def request_file(self, file_path_on_server):

        write_request = bytearray()
        write_request.append(0)
        write_request.append(1)
        filename = bytearray(file_path_on_server.encode('utf-8'))
        write_request += filename
        write_request.append(0)
        mode = bytearray(bytes(modeOctet, 'utf-8'))
        write_request += mode
        write_request.append(0)
        self.packet_buffer.append(write_request)

        self.fileName = open(file_path_on_server, 'wb')

    def process_udp_packet(self, packet_data, packet_source):

        number = self._parse_udp_packet(packet_data)

        if number == 1:

            blockNumber = struct.unpack('!H', packet_data[2:4])[0]
            blockNumber += 1
            chunk = self.fileName.read(blockSize)
            dataPacket = struct.pack(b'!2H', 3, blockNumber) + chunk
            self.packet_buffer.append(dataPacket)

            if len(chunk) < blockSize:

                print("Uploading the file to the server is completed")
                self.fileName.close()
                return 0

            return 1

        elif number == 2:

            error_code = struct.unpack('!H', packet_data[2:4])[0]
            error_msg = packet_data[4:-1]
            print("Error code: ", error_code, " Error: ", error_msg)
            self.fileName.close()
            return 0

        elif number == 3:

            blockNumber = struct.unpack('!H', packet_data[2:4])[0]
            dataBytes = packet_data[4:]
            self.fileName.write(dataBytes)
            ackPacket = struct.pack(b'!2H', 4, blockNumber)
            self.packet_buffer.append(ackPacket)

            if len(dataBytes) < blockSize:

                print("Downlading file from the server is completed")
                self.fileName.close()
                return 0

            return 1


    def _parse_udp_packet(self, packet_bytes):

        opCode = struct.unpack('!H', packet_bytes[0:2])[0]

        if opCode == self.TftpPacketType.ACK.value:

            return 1

        elif opCode == self.TftpPacketType.ERROR.value:

            return 2

        elif opCode == self.TftpPacketType.DATA.value:

            return 3

    def get_next_output_packet(self):

        return self.packet_buffer.pop(0)

    def has_pending_packets_to_be_sent(self):

        return len(self.packet_buffer) != 0



def parse_user_input(address, operation, file_name=None):

    type = TftpProcessor()

    if operation == "push":

        print(f"Attempting to upload [{file_name}]...")

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_address = (address, port)
        sock.settimeout(timeOut)

        type.upload_file(file_name)
        sock.sendto(type.get_next_output_packet(), server_address)

        while True:

            data, server = sock.recvfrom(4096)
            breaking = type.process_udp_packet(data, server)
            sock.sendto(type.get_next_output_packet(), server)

            if breaking == 0:

                type._empty_filename_used()
                break

        pass


    elif operation == "pull":

        print(f"Attempting to download [{file_name}]...")

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_address = (address, port)
        sock.settimeout(timeOut)

        type.request_file(file_name)
        sock.sendto(type.get_next_output_packet(), server_address)

        while True:

            data, server = sock.recvfrom(4096)
            breaking = type.process_udp_packet(data, server)
            sock.sendto(type.get_next_output_packet(), server_address)

            if breaking == 0:

                type._empty_filename_used()
                break

        pass

def get_arg(param_index, default=None):

    try:
        return sys.argv[param_index]
    except IndexError as e:
        if default:
            return default
        else:
            print(e)
            print(f"[FATAL] The comamnd-line argument #[{param_index}] is missing")
            exit(-1)

def check_file_name():

    script_name = os.path.basename(__file__)
    import re
    matches = re.findall(r"(\d{4}_)+lab1\.(py|rar|zip)", script_name)
    if not matches:
        print(f"[WARN] File name is invalid [{script_name}]")
    pass

def main():

   print("*" * 50)
   print("[LOG] Printing command line arguments\n", ",".join(sys.argv))
   check_file_name()
   print("*" * 50)


   # ip_address = get_arg(1, "127.0.0.1")
   # operation = get_arg(2, "push")
   # file_name = get_arg(3, "test.txt")






   command = input("Enter your Command: ")

   ip_address = get_arg(1, command.split(' ')[0])
   operation = get_arg(2, command.split(' ')[1])
   file_name = get_arg(3, command.split(' ')[2])

   parse_user_input(ip_address, operation, file_name)




if __name__ == "__main__":
    main()
