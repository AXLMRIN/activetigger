import { FC, PropsWithChildren, createContext, useContext, useEffect, useState } from 'react';

import {
  DisplayConfig,
  GenerateConfig,
  NotificationType,
  ProjectStateModel,
  SelectionConfig,
} from '../types';

// Context content
export type AppContextValue = {
  notifications: NotificationType[]; // manage notification
  selectionConfig: SelectionConfig; // selection for the next element
  generateConfig: GenerateConfig;
  displayConfig: DisplayConfig; // config for the visual
  currentProject?: ProjectStateModel | null; // current project selected
  currentScheme?: string; // scheme selected to annotate
  currentProjection?: string;
  freqRefreshSimpleModel: number; // freq to refresh active learning model
  history: string[]; // element annotated
  reFetchCurrentProject?: () => void; // update the state of the project
  phase: string;
  isComputing: boolean;
};

export const CONTEXT_LOCAL_STORAGE_KEY = 'activeTigger.context';

export const DEFAULT_CONTEXT: AppContextValue = {
  notifications: [],
  displayConfig: {
    displayContext: false,
    displayPrediction: true,
    displayHistory: false,
    frameSize: 50,
  },
  selectionConfig: {
    mode: 'deterministic',
    sample: 'untagged',
    frameSelection: false,
    frame: [],
  },
  generateConfig: { n_batch: 1, selection_mode: 'all' },
  history: [],
  freqRefreshSimpleModel: 0,
  phase: 'train',
  isComputing: false,
};
const storedContext = localStorage.getItem(CONTEXT_LOCAL_STORAGE_KEY);

// type of the context
export type AppContextType = {
  appContext: AppContextValue;
  setAppContext: React.Dispatch<React.SetStateAction<AppContextValue>>;
  resetContext: () => void;
};

export const AppContext = createContext<AppContextType>(null as unknown as AppContextType);

const _useAppContext = () => {
  const [appContext, setAppContext] = useState<AppContextValue>(
    storedContext ? (JSON.parse(storedContext) as AppContextValue) : DEFAULT_CONTEXT,
  );

  //store context in localstorage
  useEffect(() => {
    localStorage.setItem(CONTEXT_LOCAL_STORAGE_KEY, JSON.stringify(appContext));
  }, [appContext]);

  // Function to reset the context
  const resetContext = () => {
    setAppContext(DEFAULT_CONTEXT);
    localStorage.setItem(CONTEXT_LOCAL_STORAGE_KEY, JSON.stringify(DEFAULT_CONTEXT));
  };

  return {
    appContext,
    setAppContext,
    resetContext,
  };
};

export function useAppContext() {
  return useContext(AppContext);
}

export const AppContextProvider: FC<PropsWithChildren> = ({ children }) => {
  const context = _useAppContext();

  // Deal here the logic of context reset ?
  // useEffect(() => {
  //   console.log('coucou');
  // }, [context.appContext.currentScheme]);

  return <AppContext.Provider value={context}>{children}</AppContext.Provider>;
};
