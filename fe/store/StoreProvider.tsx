"use client";
import { createContext, useContext } from "react";
import { postcardStore } from "./postcardStore";

const StoreContext = createContext({
  postcardStore,
});

export const useStore = () => {
  return useContext(StoreContext);
};

export const StoreProvider = ({ children }: { children: React.ReactNode }) => {
  return (
    <StoreContext.Provider value={{ postcardStore }}>
      {children}
    </StoreContext.Provider>
  );
};
