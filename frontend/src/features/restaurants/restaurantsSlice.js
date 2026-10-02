import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import api from "../../api";

const errorMessage = (error, fallback) =>
  error.response?.data?.detail || error.message || fallback;

export const fetchRestaurants = createAsyncThunk(
  "restaurants/fetchAll",
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get("/restaurants/");
      return response.data;
    } catch (error) {
      return rejectWithValue(errorMessage(error, "Could not load restaurants."));
    }
  },
);

export const createRestaurant = createAsyncThunk(
  "restaurants/create",
  async (payload, { rejectWithValue }) => {
    try {
      const response = await api.post("/restaurants/", payload);
      return response.data;
    } catch (error) {
      return rejectWithValue(errorMessage(error, "Could not create restaurant."));
    }
  },
);

export const updateRestaurant = createAsyncThunk(
  "restaurants/update",
  async ({ id, payload }, { rejectWithValue }) => {
    try {
      const response = await api.put(`/restaurants/${id}`, payload);
      return response.data;
    } catch (error) {
      return rejectWithValue(errorMessage(error, "Could not update restaurant."));
    }
  },
);

export const deleteRestaurant = createAsyncThunk(
  "restaurants/delete",
  async (id, { rejectWithValue }) => {
    try {
      await api.delete(`/restaurants/${id}`);
      return id;
    } catch (error) {
      return rejectWithValue(errorMessage(error, "Could not delete restaurant."));
    }
  },
);

const restaurantsSlice = createSlice({
  name: "restaurants",
  initialState: { items: [], loading: false, error: null },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchRestaurants.pending, (state) => { state.loading = true; state.error = null; })
      .addCase(fetchRestaurants.fulfilled, (state, action) => { state.loading = false; state.items = action.payload; })
      .addCase(fetchRestaurants.rejected, (state, action) => { state.loading = false; state.error = action.payload; })
      .addCase(createRestaurant.fulfilled, (state, action) => { state.items.unshift(action.payload); })
      .addCase(createRestaurant.rejected, (state, action) => { state.error = action.payload; })
      .addCase(updateRestaurant.fulfilled, (state, action) => {
        const index = state.items.findIndex((item) => item.id === action.payload.id);
        if (index !== -1) state.items[index] = action.payload;
      })
      .addCase(updateRestaurant.rejected, (state, action) => { state.error = action.payload; })
      .addCase(deleteRestaurant.fulfilled, (state, action) => {
        state.items = state.items.filter((item) => item.id !== action.payload);
      })
      .addCase(deleteRestaurant.rejected, (state, action) => { state.error = action.payload; });
  },
});

export default restaurantsSlice.reducer;
