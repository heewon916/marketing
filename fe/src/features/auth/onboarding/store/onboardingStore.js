// src/features/auth/onboarding/store/onboardingStore.js
import { create } from 'zustand';

const initialState = {
  merchantId: '',
  storeId: '',

  storeName: '',
  suggestedCategory: '',
  category: '',
  ownerPersona: 'aesthetic',
  menus: [],

  selectedPlaceId: '',

  address: '',
  latitude: null,
  longitude: null,

  operatingHours: {},
};

export const useOnboardingStore = create((set, get) => ({
  ...initialState,

  setMerchantId: (merchantId) => {
    set({ merchantId });
  },

  setStoreId: (storeId) => {
    set({ storeId });
  },

  setPosSyncResult: ({
    storeId,
    storeName,
    suggestedCategory,
    menus,
  }) => {
    set({
      storeId: storeId ?? '',
      storeName: storeName ?? '',
      suggestedCategory: suggestedCategory ?? '',
      category: suggestedCategory ?? '',
      menus: menus ?? [],
    });
  },

  setStoreName: (storeName) => {
    set({ storeName });
  },

  setSuggestedCategory: (suggestedCategory) => {
    set({ suggestedCategory });
  },

  setCategory: (category) => {
    set({ category });
  },

  setOwnerPersona: (ownerPersona) => {
    set({ ownerPersona });
  },

  setSelectedPlaceId: (selectedPlaceId) => {
    set({ selectedPlaceId });
  },

  setLocation: ({ address, latitude, longitude }) => {
    set({
      address: address ?? '',
      latitude: latitude ?? null,
      longitude: longitude ?? null,
    });
  },

  setOperatingHours: (operatingHours) => {
    set({ operatingHours });
  },

  getOnboardingPayload: () => {
    const {
      storeName,
      category,
      ownerPersona,
      address,
      latitude,
      longitude,
      operatingHours,
    } = get();

    return {
      storeName,
      category,
      ownerPersona,
      address,
      latitude,
      longitude,
      operatingHours: JSON.stringify(operatingHours),
    };
  },

  resetOnboarding: () => {
    set(initialState);
  },
}));
