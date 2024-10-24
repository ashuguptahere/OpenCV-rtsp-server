# necessary imports
import gi
import cv2
import argparse

gi.require_version("Gst", "1.0")
gi.require_version("GstRtspServer", "1.0")
from gi.repository import Gst, GstRtspServer, GLib  # Use GLib instead of GObject


class SensorFactory(GstRtspServer.RTSPMediaFactory):
    def __init__(self, **properties):
        super(SensorFactory, self).__init__(**properties)
        self.cap = cv2.VideoCapture(opt.device_id)
        self.number_frames = 0
        self.fps = opt.fps
        self.duration = 1 / self.fps * Gst.SECOND
        self.launch_string = (
            "appsrc name=source is-live=true block=true format=GST_FORMAT_TIME "
            "caps=video/x-raw,format=BGR,width={},height={},framerate={}/1 "
            "! videoconvert ! video/x-raw,format=I420 "
            "! x264enc speed-preset=ultrafast tune=zerolatency "
            "! rtph264pay config-interval=1 name=pay0 pt=96".format(
                opt.image_width, opt.image_height, self.fps
            )
        )

    def on_need_data(self, src, length):
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.resize(
                    frame,
                    (opt.image_width, opt.image_height),
                    interpolation=cv2.INTER_LINEAR,
                )
                data = frame.tostring()
                buf = Gst.Buffer.new_allocate(None, len(data), None)
                buf.fill(0, data)
                buf.duration = self.duration
                timestamp = self.number_frames * self.duration
                buf.pts = buf.dts = int(timestamp)
                buf.offset = timestamp
                self.number_frames += 1
                retval = src.emit("push-buffer", buf)
                print(
                    f"pushed buffer, frame {self.number_frames}, duration {self.duration} ns"
                )
                if retval != Gst.FlowReturn.OK:
                    print(retval)

    def do_create_element(self, url):
        return Gst.parse_launch(self.launch_string)

    def do_configure(self, rtsp_media):
        self.number_frames = 0
        appsrc = rtsp_media.get_element().get_child_by_name("source")
        appsrc.connect("need-data", self.on_need_data)


class GstServer(GstRtspServer.RTSPServer):
    def __init__(self, **properties):
        super(GstServer, self).__init__(**properties)
        self.factory = SensorFactory()
        self.factory.set_shared(True)
        self.set_service(str(opt.port))
        self.get_mount_points().add_factory(opt.stream_uri, self.factory)
        self.attach(None)


parser = argparse.ArgumentParser()
parser.add_argument("--device_id", required=True, help="device id for video")
parser.add_argument("--fps", required=True, help="fps of the camera", type=int)
parser.add_argument("--image_width", required=True, help="video frame width", type=int)
parser.add_argument(
    "--image_height", required=True, help="video frame height", type=int
)
parser.add_argument("--port", default=8554, help="port to stream video", type=int)
parser.add_argument(
    "--stream_uri", default="/video_stream", help="rtsp video stream uri"
)
opt = parser.parse_args()

try:
    opt.device_id = int(opt.device_id)
except ValueError:
    pass

Gst.init(None)
server = GstServer()
loop = GLib.MainLoop()
loop.run()
