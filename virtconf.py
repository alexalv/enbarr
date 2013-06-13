import xml.etree.ElementTree as xml
import uuid

class Virtconf:
    """
    Class for libvirt xml configs creation
    Init object with vm characteristics and you will get the valid xml form of config
    """

    def __init__(self,memory="512",image="no",cpu="1",user_id="0"):
        self.memory = memory
        self.image = image
        self.cpu = cpu
        self.user_id = user_id
        self.uuid = str(uuid.uuid4())
    
    def get_uuid(self):
        return self.uuid


    def xml_form(self):
        root = xml.Element("domain")
        root.attrib["type"] = "qemu"
        root.attrib["id"] = self.uuid

        name = xml.Element("name")
        name.text=self.user_id+"."+self.uuid

        uuid = xml.Element("uuid")
        uuid.text = self.uuid

        os = xml.Element("os")
        ostype = xml.Element("type")
        ostype.attrib["arch"]="x86_64"
        ostype.text = "hvm"
        #osboot = xml.Element("boot")
        #osboot.attrib["dev"]="hd"
        os.append(ostype)
        #os.append(osboot)

        features=xml.Element("features")
        features.append(xml.Element("acpi"))
        features.append(xml.Element("apic"))
        features.append(xml.Element("pae"))
        #vcpu = xml.Element("vcpu")
        memory = xml.Element("memory")
        memory.attrib["unit"]="MB"
        memory.text = str(self.memory)

        devices = xml.Element("devices")

        emulator = xml.Element("emulator")
        emulator.text = "/usr/bin/qemu-system-x86_64"

        disk = xml.Element("disk")
        disk.attrib["type"]="file"
        disk.attrib["snapshot"]="external"

        source = xml.Element("source")
        source.attrib["file"]=self.image

        target = xml.Element("target")
        target.attrib["dev"]="hda"

        disk.append(source)
        disk.append(target)

        graphics = xml.Element("graphics")
        graphics.attrib["type"] = "vnc"
        graphics.attrib["port"] = "-1"
        #graphics.attrib["keymap"] = "en"
        graphics.attrib["autoport"] = "yes"
        graphics.attrib["listen"] = "0.0.0.0"
        graphics.attrib["passwd"] = "vnc"

        #listen = xml.Element("listen")
        #listen.attrib["type"] = "address"
        #listen.attrib["address"] = "0.0.0.0"

        #passwd = xml.Element("passwd")
        #passwd.text="vnc"

        #graphics.append(listen)
        #graphics.append(passwd)

        #interfaceN = xml.Element("interface")
        #interfaceN.attrib["type"] = "network"

        #sourceN = xml.Element("source")
        #sourceN.attrib["network"]='default'

        #interfaceN.append(sourceN)

        video = xml.Element("video")

        model = xml.Element("model")
        model.attrib["type"] = "cirrus"
        model.attrib["vram"] = "9216"
        model.attrib["heads"] = "1"

        vaddress = xml.Element("address")
        vaddress.attrib["type"] = "pci"
        vaddress.attrib["domain"] = "0x0000"
        vaddress.attrib["bus"] = "0x00"
        vaddress.attrib["slot"] = "0x02"
        vaddress.attrib["function"] = "0x0"

        video.append(model)
        video.append(vaddress)

        devices.append(disk)
        devices.append(emulator)
        devices.append(graphics)
        devices.append(video)
        #devices.append(interfaceN)

        root.append(name)
        root.append(uuid)
        root.append(os)
        root.append(features)
        #root.append(vcpu)
        root.append(memory)
        root.append(devices)


        self.xmlconf = root
        



    def xml_string(self):
        self.xml_form()
        return xml.tostring(self.xmlconf)
