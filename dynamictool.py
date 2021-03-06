import logging
import gatt
from argparse import ArgumentParser
from cmdhandler import CmdHandler
from cowdevice import CowDevice
from characteristicsmenager import CharacteristicsMenager
from utils import get_config
import sys 

config = get_config("services.yml")

parser = ArgumentParser(description=config["description"])

cm = CharacteristicsMenager(config)

cmd_handler = CmdHandler(cm, parser)
cmd_handler.add_arguments()
cmd_handler.parse_args()

logger = logging.getLogger('console')
ch = logging.StreamHandler()
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
formatter = logging.Formatter('%(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

logger.setLevel(cmd_handler.verbosity)
manager = gatt.DeviceManager(adapter_name=cmd_handler.adapter_name)
cow_device = CowDevice(
    mac_address=cmd_handler.mac_address, 
    manager=manager, 
    characteristics=cm,
    read_all=cmd_handler.read_all, 
    service_uuid=config['services']['generic']['uuid']
    )

cow_device.connect()

manager.run() 

if not cow_device.services_resolved_called:
    logger.critical("Services not resolved!")
    # enforce device disconnect to avoid device hanging on system level
    cow_device.disconnect()
    sys.exit(4)

if cow_device.write_failed != 0:
    logger.critical("Some of write chars failed!")
    # enforce device disconnect to avoid device hanging on system level
    cow_device.disconnect()
    sys.exit(5)