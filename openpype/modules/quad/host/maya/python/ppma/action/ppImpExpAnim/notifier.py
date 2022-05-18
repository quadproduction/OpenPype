import platform
import logging


def send_notification(tk, user, project_ctx, step_ctx, entity_ctx, source_published_file_id, source_published_file_name, abc_published_file_id, entity_name, mode="recap_export_on_farm", error=None, extra_values={}, logger=None):
    """
    """
    if not logger:
        logger = logging.getLogger('ppma.action.ppImpExpAnim')
        logger.setLevel(logging.DEBUG)

    logger.debug("send_notification(tk={tk}, user={user}, project_ctx={project_ctx}, step_ctx={step_ctx}, entity_ctx={entity_ctx}, source_published_file_id={source_published_file_id}, abc_published_file_id={abc_published_file_id}, entity_name={entity_name}, mode={mode})".format(tk=tk, user=user, project_ctx=project_ctx, step_ctx=step_ctx, entity_ctx=entity_ctx, source_published_file_id=source_published_file_id, abc_published_file_id=abc_published_file_id, entity_name=entity_name, mode=mode))

    # get name
    first_name = user
    try:
        first_name = user.split(' ')[0]
    except:
        pass
    # Get Workstation Name
    workstation_name = platform.node()
    # integer for published file
    if source_published_file_id:
        source_published_file_id = int(source_published_file_id)
    if abc_published_file_id:
        abc_published_file_id = int(abc_published_file_id)
    sg_user = tk.shotgun.find_one('HumanUser', [['name', 'is', user]])
    # https://wizz.shotgunstudio.com/detail/PublishedFile/14855
    # build body note
    body = "Hey %s,\n" % first_name
    if mode == "recap_export_on_farm":
        body += "Ton job vient de partir sur la farm.\n"
        if extra_values:
            if 'assets' in extra_values.keys():
                body += "La liste des Assets en export sont :\n"
                for a in extra_values['assets']:
                    body += "- *%s*\n" % a
    if mode == "export_done_on_farm":
        body += "Ton job vient de finir sur la farm. C'etait pour :\n--\n"
        body += "Shot\t: *{shot}*\n".format(shot=entity_ctx['name'])
        body += "Scene\t: *{scene}*\n".format(scene=source_published_file_name.split('.')[0])
        body += "\n"
        body += "Asset\t: *{entity_name}*\n".format(entity_name=entity_name)
    if mode == "export_done_on_local":
        body += "Ton job vient de finir sur ta machine. C'etait pour :\n--\n"
        body += "Shot\t: *{shot}*\n".format(shot=entity_ctx['name'])
        body += "Scene\t: *{scene}*\n".format(scene=source_published_file_name.split('.')[0])
        body += "\n"
        body += "Asset\t: *{entity_name}*\n".format(entity_name=entity_name)
    if mode == "export_error":
        body += "C'est la loose y a une erreur sur l'export.\n"
        body += "Le node qui a exporte est : *%s*\n a export *%s* du shot *%s*.\n" % (workstation_name, entity_name, entity_ctx['name'])
        body += "Il a published le fichier ici https://wizz.shotgunstudio.com/detail/PublishedFile/%s\n" % (abc_published_file_id)
        body += "Dans le links de la note tu retrouveras le nom de la scene qui a servie a l'export et le fichier published.\n++"
    # build links
    links = [entity_ctx]
    if source_published_file_id:
        links.append({'id': source_published_file_id, 'type': 'PublishedFile'})
    if abc_published_file_id:
        links.append({'id': abc_published_file_id, 'type': 'PublishedFile'})
    data = {}
    data["project"] = project_ctx
    data["subject"] = "ExpAnim {source_published_file_name}".format(source_published_file_name=source_published_file_name.split('.')[0])
    data["content"] = body
    data["user"] = sg_user
    data["addressings_to"] = [sg_user]
    data["note_links"] = links
    data["tag_list"] = ['auto-note']
    data["sg_note_type"] = "Internal"
    data["sg_status_list"] = "clsd"
    # Check if Note already Exist with Same Subject
    filters = [['subject', 'contains', data["subject"]], ['project.Project.id', 'is', project_ctx['id']]]
    fieldsReturn = ['id', 'replies', 'note_links']
    old_note = tk.shotgun.find_one('Note', filters, fieldsReturn)
    logger.debug("old_note : {old_note}".format(old_note=old_note))
    logger.debug("\t Old Note Filters : {filters}".format(filters=filters))
    # If Note Don't Already Exist Send Note else Reply
    if not old_note:
        logger.debug("Create Note\nData: %s" % data)
        try:
            noteResult = tk.shotgun.create('Note', data)
            logger.debug("Note Result: %s" % noteResult)
            return True
        except RuntimeError, e:
            logger.error("Error: %s" % e.args)
            return False
    else:
        # Create Reply
        dataR = {}
        dataR["content"] = data["content"]
        dataR["entity"] = old_note
        dataR["user"] = sg_user
        # create the reply
        logger.debug("Create Reply\nData: %s" % dataR)
        try:
            replyResult = tk.shotgun.create('Reply', dataR)
        except RuntimeError, e:
            logger.error("Error: %s" % e.args)
            return False
        # Link Reply and Note
        replies = old_note['replies']
        replies.append(replyResult)

        note_links = old_note['note_links']
        logger.info("Old Note note_links  : {note_links}".format(nid=old_note['id'], note_links=old_note['note_links']))
        for link in data["note_links"]:
            if link not in note_links:
                note_links.append(link)
        #  update replies and links
        logger.debug("Update Previous Note: %s\nData: %s" % (old_note['id'], data))
        updateNoteData = {
            'replies': replies,
            # 'note_links': note_links
        }
        logger.info("Create Reply Not id  : {nid}\nUpdate Data : {update_data}".format(nid=old_note['id'], update_data=updateNoteData))
        try:
            tk.shotgun.update('Note', old_note['id'], updateNoteData)
            return True
        except RuntimeError, e:
            logger.error("Error: %s" % e.args)
            return False
