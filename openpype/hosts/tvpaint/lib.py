import os
import shutil
import collections
from math import ceil
from PIL import Image, ImageDraw, ImageChops


def backwards_id_conversion(data_by_layer_id):
    """Convert layer ids to strings from integers."""
    for key in tuple(data_by_layer_id.keys()):
        if not isinstance(key, str):
            data_by_layer_id[str(key)] = data_by_layer_id.pop(key)


def get_frame_filename_template(frame_end, filename_prefix=None, ext=None):
    """Get file template with frame key for rendered files.

    This is simple template contains `{frame}{ext}` for sequential outputs
    and `single_file{ext}` for single file output. Output is rendered to
    temporary folder so filename should not matter as integrator change
    them.
    """
    frame_padding = 4
    frame_end_str_len = len(str(frame_end))
    if frame_end_str_len > frame_padding:
        frame_padding = frame_end_str_len

    ext = ext or ".png"
    filename_prefix = filename_prefix or ""

    return "{}{{frame:0>{}}}{}".format(filename_prefix, frame_padding, ext)


def get_layer_pos_filename_template(range_end, filename_prefix=None, ext=None):
    filename_prefix = filename_prefix or ""
    new_filename_prefix = filename_prefix + "pos_{pos}."
    return get_frame_filename_template(range_end, new_filename_prefix, ext)


def _calculate_in_range_frames(
    range_start, range_end,
    exposure_frames, layer_frame_end,
    output_idx_by_frame_idx
):
    """Calculate frame references in defined range.

    Function may skip whole processing if last layer frame is after range_end.
    In that case post behavior does not make sense.

    Args:
        range_start(int): First frame of range which should be rendered.
        range_end(int): Last frame of range which should be rendered.
        exposure_frames(list): List of all exposure frames on layer.
        layer_frame_end(int): Last frame of layer.
        output_idx_by_frame_idx(dict): References to already prepared frames
            and where result will be stored.
    """
    # Calculate in range frames
    in_range_frames = []
    for frame_idx in exposure_frames:
        # if the range_start is in between 2 exposure frame
        if range_start > frame_idx:
            output_idx_by_frame_idx[range_start] = frame_idx
        if range_start <= frame_idx <= range_end:
            output_idx_by_frame_idx[frame_idx] = frame_idx
            in_range_frames.append(frame_idx)

    if in_range_frames:
        first_in_range_frame = min(in_range_frames)
        # Calculate frames from first exposure frames to range end or last
        #   frame of layer (post behavior should be calculated since that time)
        previous_exposure = first_in_range_frame
        for frame_idx in range(first_in_range_frame, range_end + 1):
            if frame_idx > layer_frame_end:
                break

            if frame_idx in exposure_frames:
                previous_exposure = frame_idx
            else:
                output_idx_by_frame_idx[frame_idx] = previous_exposure

    # There can be frames before first exposure frame in range
    # First check if we don't alreade have first range frame filled
    if range_start in output_idx_by_frame_idx:
        return

    first_exposure_frame = max(exposure_frames)
    last_exposure_frame = max(exposure_frames)
    # Check if is first exposure frame smaller than defined range
    #   if not then skip
    if first_exposure_frame >= range_start:
        return

    # Check is if last exposure frame is also before range start
    #   in that case we can't use fill frames before out range
    if last_exposure_frame < range_start:
        return

    closest_exposure_frame = first_exposure_frame
    for frame_idx in exposure_frames:
        if frame_idx >= range_start:
            break
        if frame_idx > closest_exposure_frame:
            closest_exposure_frame = frame_idx

    output_idx_by_frame_idx[closest_exposure_frame] = closest_exposure_frame
    for frame_idx in range(range_start, range_end + 1):
        if frame_idx in output_idx_by_frame_idx:
            break
        output_idx_by_frame_idx[frame_idx] = closest_exposure_frame


def _cleanup_frame_references(output_idx_by_frame_idx):
    """Cleanup frame references to frame reference.

    Cleanup not direct references to rendered frame.
    ```
    // Example input
    {
        1: 1,
        2: 1,
        3: 2
    }
    // Result
    {
        1: 1,
        2: 1,
        3: 1 // Changed reference to final rendered frame
    }
    ```
    Result is dictionary where keys leads to frame that should be rendered.
    """
    for frame_idx in tuple(output_idx_by_frame_idx.keys()):
        reference_idx = output_idx_by_frame_idx[frame_idx]
        # Skip transparent frames
        if reference_idx is None or reference_idx == frame_idx:
            continue

        real_reference_idx = reference_idx
        _tmp_reference_idx = reference_idx
        while True:
            _temp = output_idx_by_frame_idx.get(_tmp_reference_idx)
            if not _temp:
                # Key outside the range, skip
                break
            if _temp == _tmp_reference_idx:
                real_reference_idx = _tmp_reference_idx
                break
            _tmp_reference_idx = _temp

        if real_reference_idx != reference_idx:
            output_idx_by_frame_idx[frame_idx] = real_reference_idx


def _cleanup_out_range_frames(output_idx_by_frame_idx, range_start, range_end):
    """Cleanup frame references to frames out of passed range.

    First available frame in range is used
    ```
    // Example input. Range 2-3
    {
        1: 1,
        2: 1,
        3: 1
    }
    // Result
    {
        2: 2, // Redirect to self as is first that reference out range
        3: 2 // Redirect to first redirected frame
    }
    ```
    Result is dictionary where keys leads to frame that should be rendered.
    """
    in_range_frames_by_out_frames = collections.defaultdict(set)
    out_range_frames = set()
    for frame_idx in tuple(output_idx_by_frame_idx.keys()):
        # Skip frames that are already out of range
        if frame_idx < range_start or frame_idx > range_end:
            out_range_frames.add(frame_idx)
            continue

        reference_idx = output_idx_by_frame_idx[frame_idx]
        # Skip transparent frames
        if reference_idx is None:
            continue

        # Skip references in range
        if reference_idx < range_start or reference_idx > range_end:
            in_range_frames_by_out_frames[reference_idx].add(frame_idx)

    for reference_idx in tuple(in_range_frames_by_out_frames.keys()):
        frame_indexes = in_range_frames_by_out_frames.pop(reference_idx)
        new_reference = None
        for frame_idx in frame_indexes:
            if new_reference is None:
                new_reference = frame_idx
            output_idx_by_frame_idx[frame_idx] = new_reference

    # Finally remove out of range frames
    for frame_idx in out_range_frames:
        output_idx_by_frame_idx.pop(frame_idx)


def _calculate_behavior_copy(
    exposure_frame, behavior, layer_frame_start, layer_frame_end,
    output_idx_by_frame_idx, frame_range, frame_count
):
    """Calculate frames based on behavior.

    Args:
        exposure_frame(list): Exposure frame use in the Hold behavior calculation.
        behavior(str): behavior of layer (enum of 4 strings).
        layer_frame_start(int): First frame of layer.
        layer_frame_end(int): Last frame of layer.
        output_idx_by_frame_idx(dict): References to already prepared frames
            and where result will be stored.
        frame_range(list): List of frames to calculate.
        frame_count(int): frame count (lenght) of the layer.
    """

    if behavior =="none":
        # Just fill all frames with None
        for frame_idx in frame_range:
            output_idx_by_frame_idx[frame_idx] = None

    elif behavior == "hold":
        # Keep exposure frame
        for frame_idx in frame_range:
            output_idx_by_frame_idx[frame_idx] = exposure_frame

    elif behavior == "repeat":
        # Loop from last/first frame of layer
        for frame_idx in frame_range:
            eq_frame_idx = ((frame_idx - layer_frame_start) % frame_count) + layer_frame_start
            output_idx_by_frame_idx[frame_idx] = eq_frame_idx

    elif behavior == "pingpong":
        half_seq_len = frame_count - 1
        seq_len = half_seq_len*2

        for frame_idx in frame_range:
            # If the frame is BEFORE the layer start
            if frame_idx < layer_frame_start:
                eq_frame_idx_offset = (layer_frame_start - frame_idx) % seq_len
                reverse = 1
                reference_frame = layer_frame_start

            # If the frame is AFTER the layer end
            else:
                eq_frame_idx_offset = (frame_idx - layer_frame_end) % seq_len
                reverse = -1
                reference_frame = layer_frame_end

            if eq_frame_idx_offset > half_seq_len:
                    eq_frame_idx_offset = (seq_len - eq_frame_idx_offset)

            output_idx_by_frame_idx[frame_idx] = reference_frame + (reverse * eq_frame_idx_offset)


def calculate_layer_frame_references(
    range_start, range_end,
    layer_frame_start,
    layer_frame_end,
    exposure_frames,
    pre_beh, post_beh
):
    """Calculate frame references for one layer based on it's data.

    Output is dictionary where key is frame index referencing to rendered frame
    index. If frame index should be rendered then is referencing to self.

    ```
    // Example output
    {
        1: 1, // Reference to self - will be rendered
        2: 1, // Reference to frame 1 - will be copied
        3: 1, // Reference to frame 1 - will be copied
        4: 4, // Reference to self - will be rendered
        ...
        20: 4 // Reference to frame 4 - will be copied
        21: None // Has reference to None - transparent image
    }
    ```

    Args:
        range_start(int): First frame of range which should be rendered.
        range_end(int): Last frame of range which should be rendered.
        layer_frame_start(int)L First frame of layer.
        layer_frame_end(int): Last frame of layer.
        exposure_frames(list): List of all exposure frames on layer.
        pre_beh(str): Pre behavior of layer (enum of 4 strings).
        post_beh(str): Post behavior of layer (enum of 4 strings).
    """
    # Output variable
    output_idx_by_frame_idx = {}
    # Skip if layer does not have any exposure frames
    if not exposure_frames:
        return output_idx_by_frame_idx

    # First calculate in range frames
    _calculate_in_range_frames(
        range_start, range_end,
        exposure_frames, layer_frame_end,
        output_idx_by_frame_idx
    )

    frame_count = (layer_frame_end - layer_frame_start) + 1
    frame_range = list(range(range_start, range_end + 1))

    # Calculate frames by pre behavior of layer
    # Skip if first layer frame is before range start
    # or Skip if first exposure frame is before range start
    if range_start < layer_frame_start or range_start < min(exposure_frames):
        # Optimize the frame range
        if range_end > layer_frame_start:
            frame_range = list(range(range_start, layer_frame_start))

        _calculate_behavior_copy(
            exposure_frame=min(exposure_frames),
            behavior=pre_beh,
            layer_frame_start=layer_frame_start,
            layer_frame_end=layer_frame_end,
            output_idx_by_frame_idx=output_idx_by_frame_idx,
            frame_range=frame_range,
            frame_count=frame_count
        )

    # Calculate frames by post behavior of layer
    # Skip if last layer frame is after range end
    # Or Skip if last exposure frame is after range end
    if range_end > layer_frame_end or range_end > max(exposure_frames):
        # Optimize the frame range
        if range_start < layer_frame_end:
            frame_range = list(range(layer_frame_end + 1, range_end + 1))

        _calculate_behavior_copy(
            exposure_frame=max(exposure_frames),
            behavior=post_beh,
            layer_frame_start=layer_frame_start,
            layer_frame_end=layer_frame_end,
            output_idx_by_frame_idx=output_idx_by_frame_idx,
            frame_range=frame_range,
            frame_count=frame_count
        )
    # Cleanup of referenced frames
    _cleanup_frame_references(output_idx_by_frame_idx)

    # Remove frames out of range
    _cleanup_out_range_frames(output_idx_by_frame_idx, range_start, range_end)

    return output_idx_by_frame_idx


def calculate_layers_extraction_data(
    layers_data,
    exposure_frames_by_layer_id,
    behavior_by_layer_id,
    range_start,
    range_end,
    skip_not_visible=True,
    filename_prefix=None,
    ext=None
):
    """Calculate extraction data for passed layers data.

    ```
    {
        <layer_id>: {
            "frame_references": {...},
            "filenames_by_frame_index": {...}
        },
        ...
    }
    ```

    Frame references contains frame index reference to rendered frame index.

    Filename by frame index represents filename under which should be frame
    stored. Directory is not handled here because each usage may need different
    approach.

    Args:
        layers_data(list): Layers data loaded from TVPaint.
        exposure_frames_by_layer_id(dict): Exposure frames of layers stored by
            layer id.
        behavior_by_layer_id(dict): Pre and Post behavior of layers stored by
            layer id.
        range_start(int): First frame of rendered range.
        range_end(int): Last frame of rendered range.
        skip_not_visible(bool): Skip calculations for hidden layers (Skipped
            by default).
        filename_prefix(str): Prefix before filename.
        ext(str): Extension which filenames will have ('.png' is default).

    Returns:
        dict: Prepared data for rendering by layer position.
    """
    # Make sure layer ids are strings
    #   backwards compatibility when layer ids were integers
    backwards_id_conversion(exposure_frames_by_layer_id)
    backwards_id_conversion(behavior_by_layer_id)

    layer_template = get_layer_pos_filename_template(
        range_end, filename_prefix, ext
    )
    output = {}
    for layer_data in layers_data:
        if skip_not_visible and not layer_data["visible"]:
            continue

        orig_layer_id = layer_data["layer_id"]
        layer_id = str(orig_layer_id)

        # Skip if does not have any exposure frames (empty layer)
        exposure_frames = exposure_frames_by_layer_id[layer_id]
        if not exposure_frames:
            continue

        layer_position = layer_data["position"]
        layer_frame_start = layer_data["frame_start"]
        layer_frame_end = layer_data["frame_end"]

        layer_behavior = behavior_by_layer_id[layer_id]

        pre_behavior = layer_behavior["pre"]
        post_behavior = layer_behavior["post"]

        frame_references = calculate_layer_frame_references(
            range_start, range_end,
            layer_frame_start,
            layer_frame_end,
            exposure_frames,
            pre_behavior, post_behavior
        )
        # All values in 'frame_references' reference to a frame that must be
        #   rendered out
        frames_to_render = set(frame_references.values())
        # Remove 'None' reference (transparent image)
        if None in frames_to_render:
            frames_to_render.remove(None)

        # Skip layer if has nothing to render
        if not frames_to_render:
            continue

        # All filenames that should be as output (not final output)
        filename_frames = (
            set(range(range_start, range_end + 1))
            | frames_to_render
        )
        filenames_by_frame_index = {}
        for frame_idx in filename_frames:
            filenames_by_frame_index[frame_idx] = layer_template.format(
                pos=layer_position,
                frame=frame_idx
            )

        # Store objects under the layer id
        output[orig_layer_id] = {
            "frame_references": frame_references,
            "filenames_by_frame_index": filenames_by_frame_index
        }
    return output


def create_transparent_image_from_source(img_size, dst_filepath):
    """Create transparent image of same type and size as source image."""
    img_obj = Image.new("RGBA", img_size, (0, 0, 0, 0))
    img_obj.save(dst_filepath)


def fill_reference_frames(frame_references, filepaths_by_frame):
    # Store path to first transparent image if there is any
    for frame_idx, ref_idx in frame_references.items():
        # Frame referencing to self should be rendered and used as source
        #   and reference indexes with None can't be filled
        if ref_idx is None or frame_idx == ref_idx:
            continue

        # Get destination filepath
        src_filepath = filepaths_by_frame[ref_idx]
        dst_filepath = filepaths_by_frame[frame_idx]

        if hasattr(os, "link"):
            os.link(src_filepath, dst_filepath)
        else:
            shutil.copy(src_filepath, dst_filepath)


def copy_render_file(src_path, dst_path):
    """Create copy file of an image."""
    if hasattr(os, "link"):
        os.link(src_path, dst_path)
    else:
        shutil.copy(src_path, dst_path)


def cleanup_rendered_layers(filepaths_by_layer_id):
    """Delete all files for each individual layer files after compositing."""
    # Collect all filepaths from data
    all_filepaths = []
    for filepaths_by_frame in filepaths_by_layer_id.values():
        all_filepaths.extend(filepaths_by_frame.values())

    # Loop over loop
    for filepath in set(all_filepaths):
        if filepath is not None and os.path.exists(filepath):
            os.remove(filepath)


def composite_rendered_layers(
    layers_data, filepaths_by_layer_id,
    range_start, range_end,
    dst_filepaths_by_frame, opacity_by_layer_id,
    cleanup=True
):
    """Composite multiple rendered layers by their position.

    Result is single frame sequence with transparency matching content
    created in TVPaint. Missing source filepaths are replaced with transparent
    images but at least one image must be rendered and exist.

    Function can be used even if single layer was created to fill transparent
    filepaths.

    Args:
        layers_data(list): Layers data loaded from TVPaint.
        filepaths_by_layer_id(dict): Rendered filepaths stored by frame index
            per layer id. Used as source for compositing.
        range_start(int): First frame of rendered range.
        range_end(int): Last frame of rendered range.
        dst_filepaths_by_frame(dict): Output filepaths by frame where final
            image after compositing will be stored. Path must not clash with
            source filepaths.
        opacity_by_layer_id(dict): Opacity stored by layer id (0-255). Used as source for compositing.
        cleanup(bool): Remove all source filepaths when done with compositing.
    """
    # Prepare layers by their position
    #   - position tells in which order will compositing happen
    layer_ids_by_position = collections.OrderedDict()
    for layer in layers_data:
        layer_ids_by_position[layer["position"]] = layer["layer_id"]

    # Sort layer positions
    sorted_layer_ids_by_position = dict(sorted(layer_ids_by_position.items(), reverse=True))

    # Prepare variable where filepaths without any rendered content
    #   - transparent will be created
    transparent_filepaths = set()
    # Store first final filepath
    first_dst_filepath = None
    # Store image size
    image_size = None

    for frame_index in range(range_start, range_end + 1):
        dst_filepath = dst_filepaths_by_frame[frame_index]
        src_files_opacity = {}

        for layer_position, layer_id in sorted_layer_ids_by_position.items():
            cur_filepath = filepaths_by_layer_id[layer_id].get(frame_index)
            if not cur_filepath:
                continue

            src_files_opacity[cur_filepath] = opacity_by_layer_id.get(layer_id, 255)

        if not src_files_opacity:
            transparent_filepaths.add(dst_filepath)
            continue

        if src_files_opacity:
            image_obj = composite_images(src_files_opacity, dst_filepath)
            if image_size is None:
                image_size = image_obj.size

    # Store first transparent filepath to be able copy it
    transparent_filepath = None
    for dst_filepath in transparent_filepaths:
        if transparent_filepath is None:
            create_transparent_image_from_source(image_size, dst_filepath)
            transparent_filepath = dst_filepath
        else:
            copy_render_file(transparent_filepath, dst_filepath)

    # Remove all files that were used as source for compositing
    if cleanup:
        cleanup_rendered_layers(filepaths_by_layer_id)


def create_layer_alpha(input_image_file, alpha_value):
    """
    Create a Luminance image based on the image alpha and the tvpp layer opacity
    Args:
        input_image_file(str): path to the image
        alpha_value(int): value of the opacity of the tvpp layer (0-255)

    Returns:
        Image: A luminance image resulting as the true alpha of the tvpp layer
    """
    #Open the input image
    _img_obj = Image.open(input_image_file)
    # Get the alpha channel
    alpha = _img_obj.convert("RGBA").getchannel('A')
    # Create a Luminance image based on the alpha value of the tvpp layer
    layer_alpha_image = Image.new("L", _img_obj.size, alpha_value)
    # mutliply the 2 luminances images
    return(ImageChops.multiply(alpha, layer_alpha_image))

def composite_images(input_files_data, output_filepath):
    """Composite images in order from passed list.

    Raises:
        ValueError: When entered list is empty.
    """
    if not input_files_data:
        raise ValueError("Nothing to composite.")

    img_obj = None
    for file_path, opacity in input_files_data.items():
        _img_obj = Image.open(file_path)
        # Create and apply a luminance mask if opacity is not 255 (or 100 in tvpp)
        if opacity < 255:
            _img_obj.putalpha(create_layer_alpha(file_path, opacity))
        if img_obj is None:
            img_obj = _img_obj
        else:
            img_obj.alpha_composite(_img_obj)
    img_obj.save(output_filepath)
    return img_obj

def rename_filepaths_by_frame_start(
    filepaths_by_frame, range_start, range_end, new_frame_start
):
    """Change frames in filenames of finished images to new frame start."""

    # Calculate frame end
    new_frame_end = range_end + (new_frame_start - range_start)
    # Create filename template
    filename_template = get_frame_filename_template(
        max(range_end, new_frame_end)
    )

    # Use different ranges based on Mark In and output Frame Start values
    # - this is to make sure that filename renaming won't affect files that
    #   are not renamed yet
    if range_start < new_frame_start:
        source_range = range(range_end, range_start - 1, -1)
        output_range = range(new_frame_end, new_frame_start - 1, -1)
    else:
        # This is less possible situation as frame start will be in most
        #   cases higher than Mark In.
        source_range = range(range_start, range_end + 1)
        output_range = range(new_frame_start, new_frame_end + 1)

    # Skip if source first frame is same as destination first frame
    new_dst_filepaths = {}
    for src_frame, dst_frame in zip(source_range, output_range):
        if not filepaths_by_frame.get(src_frame):
            continue
        src_filepath = os.path.normpath(filepaths_by_frame[src_frame])
        dirpath, src_filename = os.path.split(src_filepath)
        dst_filename = filename_template.format(frame=dst_frame)
        dst_filepath = os.path.join(dirpath, dst_filename)

        if src_filename != dst_filename:
            os.rename(src_filepath, dst_filepath)

        new_dst_filepaths[dst_frame] = dst_filepath

    return new_dst_filepaths
