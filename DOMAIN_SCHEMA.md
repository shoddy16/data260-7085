# Domain Schema — Local Restaurant Inspections

## Entity

Restaurant inspection

## Fields

| Field | Type | Required | Description |
|---|---|---|---|
| restaurantName | string | Yes | Name of the restaurant that is being inspected |
| location | string | Yes | Location or address of the restaurant |
| email | string | Yes | Email address of the person submitting the inspection |
| description | string | Yes | Description of the inspection findings |
| category | string | Yes | Overall inspection category |

## Category Values

I will be usong four values for the category field:

1. Passed
2. Conditional Pass
3. Reinspection Required
4. Violation or Failed