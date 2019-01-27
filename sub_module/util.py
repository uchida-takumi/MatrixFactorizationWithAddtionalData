#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class id_transformer:
    def __init__(self):
        """
        transform ids to the index which start from 0.
        """
        pass
    def fit(self, ids):
        """
        ARGUMETs:
            ids [array-like object]: 
                array of id of user or item.        
        """
        ids_ = sorted(list(set(ids)))
        self.id_convert_dict = {i:index for index,i in enumerate(ids_)}
    
    def transform(self, ids, unknown=None):
        """
        ARGUMETs:
            ids [array-like object]: 
                array of id of user or item.                
        """
        return [self.id_convert_dict.get(i, unknown) for i in ids]

    def fit_transform(self, ids):
        self.fit(ids)
        return self.transform(ids)
        
    def inverse_transform(self, indexes, unknown=None):
        """
        ARGUMETs:
            indexes [array-like object]: 
                array of index which are transformed                
        """
        return [get_key_from_val(self.id_convert_dict, ind) for ind in indexes]
    
    def fit_update(self, ids):
        """
        ARGUMETs:
            ids [array-like object]: 
                array of id of user or item.        
        """
        ids_ = sorted(list(set(ids)))
        ids_ = [id_ for id_ in ids_ if id_ not in self.id_convert_dict.keys()]
        now_max_id = max(self.id_convert_dict.values())
        new_id_convert_dict = {i:now_max_id+1+index for index,i in enumerate(ids_)}
        self.id_convert_dict.update(new_id_convert_dict)
    
    
        
def get_key_from_val(dict_, val, unknown=None):
    """
    dict_ = {'aa':123}
    val = 123
    get_key_from_val(dict_, val)
    > 'aa'    
    """
    list_vals = list(dict_.values())
    if val in list_vals:
        return list(dict_.keys())[list_vals.index(val)]    
    else:
        return unknown

        
    
