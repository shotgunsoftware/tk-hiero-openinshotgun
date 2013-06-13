"""
Copyright (c) 2013 Shotgun Software, Inc
----------------------------------------------------

Open selection in Shotgun
"""

from PySide import QtGui
from PySide import QtCore

import hiero.core

from tank.platform import Application


class HieroOpenInShotgun(Application):
    def init_app(self):
        self.properties = {
            'sender': None,
        }
        self.engine.register_command("Open in Shotgun", self.callback, self.properties)

    def callback(self):
        # grab the current selection from the view that triggered the event
        sender = self.properties['sender']
        selection = sender.selection()

        # collect shots by sequence
        shots = {}
        for item in selection:
            if not isinstance(item, hiero.core.TrackItem):
                continue
            sequence = item.parent().parent()
            shots.setdefault(sequence.name(), []).append(item.name())

        # build up a shotgun filter to pull back the appropriate shots
        seq_filts = []
        for (seq, entries) in shots.iteritems():
            seq_filts.append({
                'logical_operator': 'and',
                'conditions': [
                    {'path': 'sg_sequence.Sequence.code', 'relation': 'is', 'values': [seq]},
                    {'path': 'code', 'relation': 'in', 'values': list(set(entries))},
                ]
            })

        filt = {
            'logical_operator': 'and',
            'conditions': [
                {'path': 'project', 'relation': 'is', 'values':[self.context.project]},
                {'logical_operator': 'or', 'conditions': seq_filts, }
            ]
        }

        sg_shots = self.shotgun.find('Shot', filt, fields=['code'])

        # and open each returned shot in the browser
        for shot in sg_shots:
            context = self.tank.context_from_entity(shot['type'], shot['id'])
            if context:
                QtGui.QDesktopServices.openUrl(QtCore.QUrl(context.shotgun_url))
