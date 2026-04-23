import mne
import re


def make_epochs(raw_fname, keep_eve=None):
    # Load the raw data
    raw = mne.io.read_raw_eeglab(raw_fname, preload=True)
    # Rename channesl to match montage
    raw.rename_channels({'CZ': 'Cz'})
    # Set montage
    montage = mne.channels.make_standard_montage("standard_1020")
    raw.set_montage(montage)
    
    # Extract events from annotations
    events, event_id = mne.events_from_annotations(raw)
    
    # Events have a structured name, for example F/b1/A/w1/mi
    # These letters stands for:
    # F, T: Familiarization, Test
    # b1, b2, ...: Block 1, Block 2, ...
    # A, B: Condition A, B
    # w1, w2, ...: 1st repetition of word, 2nd repetition of word, ...
    # mi, pe: Pseudoword mita, pelu
    
    # Select events of interest
    if keep_eve is not None:
        kept_event_id = {}
        for k in event_id.keys():
            if re.search(keep_eve, k):
                kept_event_id[k] = event_id[k]
        event_id = kept_event_id
    
    # Trim events matrix to only include events of interest
    events = events[[e[2] in event_id.values() for e in events]]
    
    # Make epochs
    epochs = mne.Epochs(raw, events, event_id=event_id, tmin=-.5, tmax=1.2, 
                        baseline=(None, 0), preload=True)
    
    return epochs


def sel_epo_by_eve(epochs, keep_eve):
    # Select epochs of interest
    sel_eve, idx_eve = [], []
    for i, (k, v) in enumerate(epochs.event_id.items()):
        if re.search(keep_eve, k):
            sel_eve.append(v)
            idx_eve.append(i)
    assert epochs.events[idx_eve, -1].tolist() == sel_eve, "Selected events do not match the events in epochs"
    sel_epochs = epochs[idx_eve].copy()
    
    return sel_epochs


if __name__ == "__main__":
    from guanas_rue.config import DATA_DIR
    
    data_fname = f"{DATA_DIR}/sub-050cp208_ses-01_task-remind_run-01_eeg-preprocessed_cut_30s_fixed.set"
    keep_eve = '(F/b|T/b)'
    
    epochs = make_epochs(data_fname, keep_eve)
    # sel_epochs = sel_epo_by_eve(epochs, '.*w1.*mi')
    
    sel_epo_by_eve(epochs, 'T.*mi')
    # First vs second occurrence across familiarization blocks
    fam_first = sel_epo_by_eve(epochs, 'F.*w1')
    fam_second = sel_epo_by_eve(epochs, 'F.*w2')
    mne.viz.plot_compare_evokeds([fam_first.average(), fam_second.average()])
    mne.viz.plot_evoked_topo([fam_first.average(), fam_second.average()])
    # diff_fam = mne.combine_evoked([fam_first.average(), fam_second.average()], weights=[1, -1])
    # diff_fam.plot_topo()

    # Mita vs Pelu across first words in test blocks
    test_mi = sel_epo_by_eve(epochs, 'T.*w1.*mi')
    test_pe = sel_epo_by_eve(epochs, 'T.*w1.*pe')
    mne.viz.plot_compare_evokeds([test_mi.average(), test_pe.average()])
    mne.viz.plot_evoked_topo([test_mi.average(), test_pe.average()])