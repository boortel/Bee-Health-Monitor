import numpy as np
import cv2

from background import BackgroundModel


class State:
    """Track states
    """
    Arrived = 1
    Left = 2
    Accounted = 3
    Expired = 4


class Track:
    """Single bee track
    """
    def __init__(self, max_age=5):
        """
        Args:
            max_age (int, optional): Maximum pending age, track is dismissed after reaching its max age. Defaults to 5.
        """
        self.state = State.Arrived
        self.max_age = max_age
        self.age = 0

    def update(self):
        """Update track age
        """
        self.age += 1
        # set as Expired if crossed maximum age
        if self.age > self.max_age:
            self.state = State.Expired
    
    def is_left(self):
        """
        Returns:
            bool: left flag
        """
        return self.state == State.Left

    def is_valid(self):
        """Track is valid if it's not expired or already accounted for

        Returns:
            bool: validity flag
        """
        return (self.state == State.Arrived) or (self.state == State.Left)


class Section:
    """Tunnel section
    """
    def __init__(self, n_keep=10, track_max_age=5, arrived_threshold=0.3, left_threshold=-0.3):
        """
        Args:
            n_keep (int, optional): number of kept information from previous time steps. Defaults to 10.
            track_max_age (int, optional): maximum track age, refer to Track. Defaults to 5.
            arrived_threshold (float, optional): classification threshold for arrival indicator. Defaults to 0.3.
            left_threshold (float, optional): classification threshold for departure indicator. Defaults to -0.3.
        """
        self.n_keep = n_keep
        self.ratios = list()

        self.arrived_threshold = arrived_threshold
        self.left_threshold = left_threshold

        self.track_max_age = track_max_age
        self.tracks = list()

    def update(self, mask, output='diff'):
        """Update section from motion mask

        Args:
            mask (numpy.ndarray): motion boolean mask
            output (str, optional): output differentiation results or classification results, outputs differentiation
                                    on "diff", classification result otherwise. Defaults to "diff".

        Returns:
            float: output class or derivative for viz purposes
        """
        # firstly update all tracks
        self.update_tracks()
        # calculate fill ratio
        ratio = np.count_nonzero(mask) / mask.size
        self.ratios.append(ratio)
        # check for maximum data length
        if len(self.ratios) > self.n_keep:
            self.ratios = self.ratios[len(self.ratios)-self.n_keep:]
        # calculate derivative and threshold it
        derivative = self.diff(order='first')
        if derivative > self.arrived_threshold:
            # classified as bee arrival, create new track
            cls = 1
            self.tracks.append(Track(max_age=self.track_max_age))
        elif derivative < self.left_threshold:
            # classified as bee departure, set the oldest arrival track as left
            cls = -1
            for track in self.tracks:
                if track.state == State.Arrived:
                    track.state = State.Left
        else:
            # no event
            cls = 0
        return derivative if output == 'diff' else cls

    def remove_invalid_tracks(self):
        """Removes invalid tracks
        """
        self.tracks = [track for track in self.tracks if track.is_valid()]

    def update_tracks(self):
        """Update all existing tracks
        """
        # update all tracks and remove expired and accounted tracks
        for track in self.tracks:
            track.update()
        self.remove_invalid_tracks()

    def diff(self, order='first'):
        """Calculate differentiation from last valid time step

        Args:
            order (str, optional): Order of diff, either "first" or "second". Defaults to 'first'.

        Returns:
            float: diff result
        """
        diff_fn = {
            'first': lambda x: (0 if len(x) < 2 else x[-1] - x[-2]),
            'second': lambda x: (0 if len(x) < 3 else x[-3] - 2*x[-2] + x[-1]),
        }
        result = diff_fn[order](self.ratios)
        return result


class Tunnel:
    """Single tunnel tracker
    """
    def __init__(self, x_boundaries, sections=4, track_max_age=5, arrived_threshold=0.3, left_threshold=-0.3, background_init_frame=None):
        """s:
            x_boundaries (tuple(int, int)): tunnel's x-axis boundaries on input frames
            sections (int, optional): number of sections the tunnel will be split on along the y-axis. Defaults to 4.
            track_max_age (int, optional): maximum track age, refer to Track. Defaults to 5.
            arrived_threshold (float, optional): classification threshold for arrival indicator. Defaults to 0.3.
            left_threshold (float, optional): classification threshold for departure indicator. Defaults to -0.3.
            background_init_frame (numpy.ndarray, optional): dynamic model initial frame. Defaults to None.
        """
        self.bins = x_boundaries
        self.n_sections = sections

        self.sections = [Section(track_max_age=track_max_age, arrived_threshold=arrived_threshold, left_threshold=left_threshold) for _ in range(sections)]
        if background_init_frame is not None:
            background_init_frame = background_init_frame[20:, self.bins[0]:self.bins[1], ...]
            background_init_frame = cv2.cvtColor(background_init_frame, cv2.COLOR_BGR2GRAY)
        self.dyn_model = BackgroundModel(50, 50, 30, 5000, background_init_frame=background_init_frame)

        self.bee_counter = {'up': 0, 'down': 0}

    def update(self, img, output='diff'):
        """Update on next time step

        Args:
            img (numpy.ndarray): BGR frame
            output (str, optional): output differentiation results or classification results, refer to Section. Defaults to "diff".

        Returns:
            list: list of outputs from individual section updates, for viz purposes
        """
        # segment tunnel from image and convert to gray
        img = img[20:, self.bins[0]:self.bins[1], ...]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # update dynamic model
        self.dyn_model.update(gray)
        # get motion mask and split the mask into sections
        mask = self.dyn_model.get_mask(gray)
        splits = np.split(mask, self.n_sections, axis=0)
        # update all sections with split masks
        outputs = [section.update(split, output=output) for section, split in zip(self.sections, reversed(splits))]
        # try to assign tracks
        self.assign_tracks()
        return outputs
    
    def assign_tracks(self):
        """Try to assign tracks from sections to bee traveling upwards or downwards
        """
        tracks_to_assign = list()
        for section in self.sections:
            for track in section.tracks:
                # if section contains unaccounted departured bee, save the track and continue with next section
                if track.state == State.Left:
                    tracks_to_assign.append(track)
                    break
                # if section does not contain unaccounted departured bee, terminate assignment
            else:
                return
        # if found departured bee in all sections, set all selected tracks as accounted
        for track in tracks_to_assign:
            track.state = State.Accounted
        # check track ages and classify direction
        key = 'up' if tracks_to_assign[0].age < tracks_to_assign[-1].age else 'down'
        self.bee_counter[key] += 1
        for section in self.sections:
            section.remove_invalid_tracks()
