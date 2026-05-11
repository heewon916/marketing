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
    console.log('[onboardingStore] merchantId:', merchantId);
    set({ merchantId });
  },

  setStoreId: (storeId) => {
    console.log('[onboardingStore] storeId:', storeId);
    set({ storeId });
  },

  setPosSyncResult: ({
    storeId,
    storeName,
    suggestedCategory,
    menus,
  }) => {
    const nextState = {
      storeId: storeId ?? '',
      storeName: storeName ?? '',
      suggestedCategory: suggestedCategory ?? '',
      category: suggestedCategory ?? '',
      menus: menus ?? [],
    };

    console.log('[onboardingStore] POS sync result:', nextState);

    set(nextState);
  },

  setStoreName: (storeName) => {
    console.log('[onboardingStore] storeName:', storeName);
    set({ storeName });
  },

  setSuggestedCategory: (suggestedCategory) => {
    console.log('[onboardingStore] suggestedCategory:', suggestedCategory);
    set({ suggestedCategory });
  },

  setCategory: (category) => {
    console.log('[onboardingStore] category:', category);
    set({ category });
  },

  setOwnerPersona: (ownerPersona) => {
    console.log('[onboardingStore] ownerPersona:', ownerPersona);
    set({ ownerPersona });
  },

  setSelectedPlaceId: (selectedPlaceId) => {
    console.log('[onboardingStore] selectedPlaceId:', selectedPlaceId);
    set({ selectedPlaceId });
  },

  setLocation: ({ address, latitude, longitude }) => {
    const nextState = {
      address: address ?? '',
      latitude: latitude ?? null,
      longitude: longitude ?? null,
    };

    console.log('[onboardingStore] location:', nextState);

    set(nextState);
  },

  setOperatingHours: (operatingHours) => {
    console.log('[onboardingStore] operatingHours:', operatingHours);
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

    const payload = {
      storeName,
      category,
      ownerPersona,
      address,
      latitude,
      longitude,
      operatingHours: JSON.stringify(operatingHours),
    };

    console.log('[onboardingStore] final payload:', payload);
    console.log(
      '[onboardingStore] operatingHours type:',
      typeof payload.operatingHours
    );

    return payload;
  },

  resetOnboarding: () => {
    console.log('[onboardingStore] reset');
    set(initialState);
  },
}));
