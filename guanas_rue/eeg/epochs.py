import mne
import re
import os
import xarray as xr
xr.set_options(keep_attrs=True)


def make_epochs(raw_fname, keep_eve=None, twin=(-.5, 1.2), bline=(None, 0),
                filter=None):
    # Load the raw data
    raw = mne.io.read_raw_eeglab(raw_fname, preload=True)
    # Rename channesl to match montage
    if 'CZ' in raw.ch_names:
        raw.rename_channels({'CZ': 'Cz'})
    # Set montage
    montage = mne.channels.make_standard_montage("standard_1020")
    raw.set_montage(montage)
    
    # Set subject id in info
    sub_id = raw_fname.split(os.sep)[-1].split('_')[0]
    raw.info['subject_info'] = {'his_id': sub_id}
    
    # Filter data if specified
    if filter is not None:
        raw.filter(filter[0], filter[1], fir_design='firwin')
    
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
    epochs = mne.Epochs(raw, events, event_id=event_id, tmin=twin[0], 
                        tmax=twin[1], baseline=bline, preload=True)
    
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


def build_epo_dataset(epochs_list):
    ds_epochs = []
    for epo in epochs_list:
        da_epo = xr.DataArray(epo.get_data(), 
                              dims=['epoch', 'channel', 'time'],
                              coords={'epoch': range(epo.events.shape[0]), 
                                      'channel': epo.ch_names, 
                                      'time': epo.times})
        # Add additional information as coordinates
        sbj_id = epo.info['subject_info']['his_id']
        sbj_id_epo = [sbj_id] * epo.events.shape[0]
        da_epo = da_epo.assign_coords(ep_type=('epoch', list(epo.event_id.keys())))
        da_epo = da_epo.assign_coords(sbj=('epoch', sbj_id_epo))
        da_epo = da_epo.assign_attrs({'sfreq': epo.info['sfreq']})
        # Add name to the DataArray
        da_epo.name = sbj_id
        # Append to the list of DataArrays
        ds_epochs.append(da_epo)
    # Concatenate all DataArrays into a single Dataset, empty channels will be fulled with nans
    ds_epochs = xr.concat(ds_epochs, dim='epoch', join='outer')
    return ds_epochs


if __name__ == "__main__":
    from guanas_rue.config import DATA_DIR
    from guanas_rue.io.io import get_files
    
    # -- Example usage --
    # data_fname = f"{DATA_DIR}/sub-050cp208_ses-01_task-remind_run-01_eeg-preprocessed_cut_30s_fixed.set"
    # keep_eve = '(F/b|T/b)'
    
    # epochs = make_epochs(data_fname, keep_eve)
    # # sel_epochs = sel_epo_by_eve(epochs, '.*w1.*mi')
    
    # sel_epo_by_eve(epochs, 'T.*mi')
    # # First vs second occurrence across familiarization blocks
    # fam_first = sel_epo_by_eve(epochs, 'F.*w1')
    # fam_second = sel_epo_by_eve(epochs, 'F.*w2')
    # mne.viz.plot_compare_evokeds([fam_first.average(), fam_second.average()])
    # mne.viz.plot_evoked_topo([fam_first.average(), fam_second.average()])
    # # diff_fam = mne.combine_evoked([fam_first.average(), fam_second.average()], weights=[1, -1])
    # # diff_fam.plot_topo()

    # # Mita vs Pelu across first words in test blocks
    # test_mi = sel_epo_by_eve(epochs, 'T.*w1.*mi')
    # test_pe = sel_epo_by_eve(epochs, 'T.*w1.*pe')
    # mne.viz.plot_compare_evokeds([test_mi.average(), test_pe.average()])
    # mne.viz.plot_evoked_topo([test_mi.average(), test_pe.average()])
    
    # -- Loop through all files --
    fam_first, fam_second = [], []
    test_fam, test_new = [], []
    file_names = get_files(f"{DATA_DIR}/", ext=".set")
    keep_eve = '(F/b|T/b)'
    for fname in file_names:
        epo = make_epochs(fname, keep_eve)
        fam_first.append(sel_epo_by_eve(epo, 'F.*w1'))
        fam_second.append(sel_epo_by_eve(epo, 'F.*w2'))
        if 'mi' in list(epo.event_id.keys())[0]:
            test_fam.append(sel_epo_by_eve(epo, 'T.*w1.*mi'))
            test_new.append(sel_epo_by_eve(epo, 'T.*w1.*pe'))
        elif 'pe' in list(epo.event_id.keys())[0]:
            test_fam.append(sel_epo_by_eve(epo, 'T.*w1.*pe'))
            test_new.append(sel_epo_by_eve(epo, 'T.*w1.*mi'))
        else:
            pass
    
    fam_first = build_epo_dataset(fam_first)
    fam_second = build_epo_dataset(fam_second)
    test_fam = build_epo_dataset(test_fam)
    test_new = build_epo_dataset(test_new)
    
    evks = []
    comments = ['Fam W1', 'Fam W2', 'Test familiar', 'Test new']
    for ds, c in zip([fam_first, fam_second, test_fam, test_new], comments):
        mean = ds.groupby('sbj').mean(dim='epoch').mean(dim='sbj')
        info = mne.create_info(ch_names=ds.channel.values.tolist(), 
                               sfreq=ds.attrs['sfreq'], ch_types='eeg')
        evk = mne.EvokedArray(mean, info, 
                              tmin=ds.time.values[0], comment=c)
        montage = mne.channels.make_standard_montage("standard_1020")
        evk.set_montage(montage)
        evks.append(evk)

    mne.viz.plot_compare_evokeds([evks[0], evks[1]])
    mne.viz.plot_evoked_topo([evks[0], evks[1]])
    mne.viz.plot_compare_evokeds([evks[2], evks[3]])
    mne.viz.plot_evoked_topo([evks[2], evks[3]])
    
    times = [0.25, 0., 0.23, 0.29, 0.33, 0.49, 0.59]
    for evk in evks:
        mne.viz.plot_evoked_topomap(evk, times=times, average=None,#0.05, 
                                    ch_type='eeg', sensors=True, vlim=(-10,10),
                                    show_names=True, show=True)
    
    breakpoint()