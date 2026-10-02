import { configureStore } from "@reduxjs/toolkit";
import inspectionsReducer from "../features/inspections/inspectionsSlice";
import restaurantsReducer from "../features/restaurants/restaurantsSlice";

export const store = configureStore({
  reducer: {
    inspections: inspectionsReducer,
    restaurants: restaurantsReducer,
  },
});
