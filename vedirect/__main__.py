"""
CLI Entry point
"""
import argparse
import datetime
import time

from vedirect.influxdb import influx
from vedirect.vedirect import Vedirect
from influxdb import InfluxDBClient

influx_client = None
influx_db = None
PUBLISH_INTERVAL=30.0 # publish interval in seconds
STATUS_FILENAME="/tmp/victron_status.json"
next_publish_time = datetime.datetime.now()


def main():
    """
    Invoke the parser
    :return:
    """
    parser = argparse.ArgumentParser(description='Parse VE.Direct serial data')
    parser.add_argument('-i', '--influx', help='Influx DB host')
    parser.add_argument('-d', '--database', help='InfluxDB database')
    parser.add_argument('-p', '--port', help='Serial port')
    args = parser.parse_args()

    global influx_db, influx_client
    print("Connecting to InfluxDB")
    influx_client = InfluxDBClient(host=args.influx, port=8086)
    influx_db = args.database
    if influx_client:
        print("Connected to InfluxDB %s" % args.influx)
    else:
        print("Could not connect to InfluxDB %s" % args.influx)

    while True:
        # Loop and try to recover by re-opening / re-initializing the Serial port
        try:
            ve = Vedirect(args.port)
            ve.read_data_callback(on_victron_data_callback)
        except  Exception as e:
            print("Exception occurred in main loop: %s" % str(e))
            print("Waiting a bit for recovery (e.g. Interface %s becoming available again)" % args.port)
            time.sleep(5.0)

def on_victron_data_callback(data):
    global next_publish_time

    if datetime.datetime.now() > next_publish_time:
        measurements = influx.measurements_for_packet(data)
        influx_client.write_points(measurements, database=influx_db)
        next_publish_time = datetime.datetime.now() + datetime.timedelta(seconds=PUBLISH_INTERVAL)
        print(measurements)
        # Also print latest status to file for easy access
        with open(STATUS_FILENAME , 'w') as status_file:
            status_file.write(repr(measurements))
            status_file.write("\n")

if __name__ == "__main__":
    main()
