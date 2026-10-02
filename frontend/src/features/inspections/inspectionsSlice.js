import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import api from "../../api";

const errorMessage = (error, fallback) =>
  error.response?.data?.detail || error.message || fallback;

export const fetchInspections = createAsyncThunk(
  "inspections/fetchAll",
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get("/inspections/");
      return response.data;
    } catch (error) {
      return rejectWithValue(errorMessage(error, "Could not load inspections."));
    }
  },
);

export const createInspection = createAsyncThunk(
  "inspections/create",
  async (payload, { rejectWithValue }) => {
    try {
      const response = await api.post("/inspections/", payload);
      return response.data;
    } catch (error) {
      return rejectWithValue(errorMessage(error, "Could not create inspection."));
    }
  },
);

export const updateInspection = createAsyncThunk(
  "inspections/update",
  async ({ id, payload }, { rejectWithValue }) => {
    try {
      const response = await api.put(`/inspections/${id}`, payload);
      return response.data;
    } catch (error) {
      return rejectWithValue(errorMessage(error, "Could not update inspection."));
    }
  },
);

export const deleteInspection = createAsyncThunk(
  "inspections/delete",
  async (id, { rejectWithValue }) => {
    try {
      await api.delete(`/inspections/${id}`);
      return id;
    } catch (error) {
      return rejectWithValue(errorMessage(error, "Could not delete inspection."));
    }
  },
);

const inspectionsSlice = createSlice({
  name: "inspections",
  initialState: { items: [], loading: false, error: null },
  reducers: { clearInspectionError: (state) => { state.error = null; } },
  extraReducers: (builder) => {
    builder
      .addCase(fetchInspections.pending, (state) => { state.loading = true; state.error = null; })
      .addCase(fetchInspections.fulfilled, (state, action) => { state.loading = false; state.items = action.payload; })
      .addCase(fetchInspections.rejected, (state, action) => { state.loading = false; state.error = action.payload; })
      .addCase(createInspection.fulfilled, (state, action) => { state.items.unshift(action.payload); })
      .addCase(createInspection.rejected, (state, action) => { state.error = action.payload; })
      .addCase(updateInspection.fulfilled, (state, action) => {
        const index = state.items.findIndex((item) => item.id === action.payload.id);
        if (index !== -1) state.items[index] = action.payload;
      })
      .addCase(updateInspection.rejected, (state, action) => { state.error = action.payload; })
      .addCase(deleteInspection.fulfilled, (state, action) => {
        state.items = state.items.filter((item) => item.id !== action.payload);
      })
      .addCase(deleteInspection.rejected, (state, action) => { state.error = action.payload; });
  },
});

export const { clearInspectionError } = inspectionsSlice.actions;
export default inspectionsSlice.reducer;
