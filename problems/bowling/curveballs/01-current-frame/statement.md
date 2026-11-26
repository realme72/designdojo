# Current frame

The lane display shows which frame the bowler is in. Add `current_frame()`: the number
(1–10) of the frame the **next** roll belongs to. A frame is finished after a strike or two
rolls; the 10th frame stays current until the game is over, and stays 10 afterwards.

*Interviewer's question:* is "frame" a real object in your design, or derived from rolls?
