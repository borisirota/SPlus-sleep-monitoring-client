import bluetooth
import shutil
from struct import unpack

types = [
	"PACKET_TYPE_CALL",
	"PACKET_TYPE_RETURN",
	"PACKET_TYPE_BIO_32",
	"PACKET_TYPE_ENV_1",
	"PACKET_TYPE_BIO_64",
	"PACKET_TYPE_ENV_60",
	"PACKET_TYPE_APP_LOAD",
	"PACKET_TYPE_COMPRESSED_DATA",
	"PACKET_TYPE_NOTE_STOP_BROWNOUT",
	"PACKET_TYPE_NOTE_STOP_WATCHDOG",
	"PACKET_TYPE_NOTE_STOP_RESET",
	"PACKET_TYPE_NOTE_STOP_TIMEOUT",
	"PACKET_TYPE_NOTE_RTC_UNAVAILABLE",
	"PACKET_TYPE_NOTE_RESUME",
	"PACKET_TYPE_NOTE_STORE_FOREIGN",
	"PACKET_TYPE_NOTE_STORE_LOCAL",
	"PACKET_TYPE_NOTE_HEARTBEAT",
	"PACKET_TYPE_NOTE_ILLUMINANCE_CHANGE",
	"PACKET_TYPE_NOTE_BIO_1",
	"PACKET_TYPE_NOTE_ENV_1",
	"PACKET_TYPE_NOTE_FW_UPGRADE",
	"PACKET_TYPE_FW_LOAD_END",
	"PACKET_TYPE_MAX_VLP"
]

address = None

# discover devices with names, and find the S+ address
#devices = bluetooth.discover_devices(lookup_names=True)
#for addr, name in devices:
	#if name.find("ResMed") != -1:
		#address = addr
		#break

address = "5C:31:3E:6C:B1:DF"

if address == None:
	raise Exception("Device not found!")

print "Found device: %s" % address

uuid = "00001101-0000-1000-8000-00805F9B34FB"
service = bluetooth.find_service(uuid = uuid, address = address)[0]

port = service["port"]
name = service["name"]
host = service["host"]

print("connecting to \"%s\" on %s" % (name, host))

sock=bluetooth.BluetoothSocket( bluetooth.RFCOMM )
sock.connect((host, port))

print("connected. sending params")

#which means: tv@o{"id":116,"jsonrpc":"2.0","method":"requestSession","params":{"guid":"80581825-BBA6-44DD-9B52-6144F2566771"}}
params = "01037476024001016f7b226964223a3131362c226a736f6e727063223a22322e30222c226d6574686f64223a227265717565737453657373696f6e222c22706172616d73223a7b2267756964223a2238303538313832352d424241362d343444442d394235322d363134344632353636373731227d7de400".decode("hex")
sock.send(params)

#get_serial_number = "01037644024001013d7b226964223a3131382c226a736f6e727063223a22322e30222c226d6574686f64223a2267657453657269616c4e756d62657253656e736f72227dba00".decode("hex")
#sock.send(get_serial_number)

start_stream_real = "01037762024001015b7b226964223a3131392c226a736f6e727063223a22322e30222c226d6574686f64223a22737461727453747265616d222c22706172616d73223a7b22737263223a225245414c222c226e5469636b73223a3130303030307d7df800".decode("hex")
sock.send(start_stream_real)
print("sent! now receiving...")

def decompress_light(val):
    if val >= 64:
        if val >= 96:
            if val >= 128:
                if val >= 160:
                    if val >= 192:
                        if val >= 240:
                            if val >= 255:
                                return 6000
                            else:
                                return (((val + -240) * 128) + 4096)
                        else:
                            return (((val + -192) * 64) + 1024)
                    else:
                        return (((val + -160) * 16) + 512)
                else:
                    return (((val - 128) * 8) + 256)
            else:
                return (((val - 96) * 4) + 128)
        else:
            return (((val - 64) * 2) + 64)
    else:
        return val

bio_data = []
bio_data2 = []

def dump_bio():
	global bio_data, bio_data2

	if len(bio_data) > 255:
		bio_data = bio_data[-255:]
	if len(bio_data2) > 255:
		bio_data2 = bio_data2[-255:]

	f = file("plot.dat.tmp", "w")
	f.write("\n".join(str(x) for x in bio_data))
	f.close()

	shutil.move("plot.dat.tmp", "plot.dat")

	f = file("plot2.dat.tmp", "w")
	f.write("\n".join(str(x) for x in bio_data2))
	f.close()

	shutil.move("plot2.dat.tmp", "plot2.dat")

def handle_env(buff):
	temperature = int(float(ord(buff[0])) / 4.0)
	light_raw = ord(buff[1])
	light = decompress_light(light_raw)
	print "env temperature is %f, light_raw: %d, light: %d" % (temperature, light_raw, light)

def handle_bio(buff):
	global bio_data

	val1 = ord(buff[0]) | (ord(buff[1]) << 8)
	val2 = ord(buff[2]) | (ord(buff[3]) << 8)

	bio_data.append(val1)
	bio_data2.append(val2)
	dump_bio();

	print "bio val1: %d val2: %d" % (val1, val2)
	pass

while True:
	data = sock.recv(1024)
	data = data[1:]
	count = len(data)
	buff = data[8:count-1]
	packet_type = ord(data[0])
	packet_type_str = types[packet_type]
	packet_number = ord(data[1])
	checksum = ord(data[count-1])
	sample_count = unpack("<I", data[4:8])[0]

	if packet_type_str == "PACKET_TYPE_NOTE_ENV_1":
		handle_env(buff)
	elif packet_type_str == "PACKET_TYPE_NOTE_BIO_1":
		handle_bio(buff)
	else:
		print "got %d bytes, type: %s, number: %d, sample_count: %d, checksum: %d, buf len: %d" % (len(data), packet_type_str, packet_number, sample_count, checksum, len(buff))
		print buff

sock.close()