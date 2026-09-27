/* Read-only capture for the isolated MPI ownership illustration build.
 * Included by capture_mpi_mesh.py in a frozen source copy, never by default.
 * Records the first predictor/corrector pair and actual MPI flux packets.
 */
#if !defined(TWODIMS) || !defined(RD_RK2_SPLIT_STAGES) || defined(RD_ALE_EQUALSTEP) || defined(RD_HIERARCHICAL_TIMESTEPS)
#error "This illustration capture is for static equal-step split RD only."
#endif

static int rd_capture_call = -1;
static int rd_capture_enabled = 0;
static FILE *rd_capture_evaluations = NULL;

static FILE *rd_capture_open(const char *kind)
{
  char path[4096];
  snprintf(path, sizeof(path), "%smpi_mesh/call_%02d_rank_%02d_%s.csv", All.OutputDir,
           rd_capture_call, ThisTask, kind);
  FILE *fp = fopen(path, "w");
  if(fp == NULL)
    terminate_program("could not open MPI mesh capture output");
  fprintf(fp, "# time=%.17g ti=%lld rank=%d ranks=%d box_x=%.17g box_y=%.17g\n",
          All.Time, (long long)All.Ti_Current, ThisTask, NTask, boxSize_X, boxSize_Y);
  return fp;
}

static void rd_capture_begin(tessellation *T, const struct rd_element_set *set)
{
  rd_capture_call++;
  const char *enabled = getenv("RD_MPI_MESH_DUMP");
  rd_capture_enabled = enabled != NULL && strcmp(enabled, "1") == 0 && rd_capture_call < 2;
  if(!rd_capture_enabled)
    return;

  FILE *fp = rd_capture_open("nodes");
  fprintf(fp, "id,rank,index,x,y,timebin\n");
  for(int i = 0; i < NumGas; i++)
    fprintf(fp, "%llu,%d,%d,%.17g,%.17g,%d\n", (unsigned long long)P[i].ID, ThisTask, i,
            P[i].Pos[0], P[i].Pos[1], P[i].TimeBinHydro);
  fclose(fp);

  fp = rd_capture_open("triangles");
  fprintf(fp, "rank,slot,dt_index,active,area");
  for(int j = 0; j < 3; j++)
    fprintf(fp, ",id%d,rank%d,dp%d,index%d,originalindex%d,x%d,y%d", j, j, j, j, j, j, j);
  fprintf(fp, "\n");
  for(int i = 0; i < set->n; i++)
    {
      int triangle = set->element[i];
      fprintf(fp, "%d,%d,%d,%d,%.17g", ThisTask, i, triangle, (int)set->active[i], set->normals[i].area);
      for(int j = 0; j < 3; j++)
        {
          int p = T->DT[triangle].p[j];
          const point *v = &T->DP[p];
          fprintf(fp, ",%llu,%d,%d,%d,%d,%.17g,%.17g", (unsigned long long)v->ID, v->task,
                  p, v->index, v->originalindex, v->x, v->y);
        }
      fprintf(fp, "\n");
    }
  fclose(fp);
  rd_capture_evaluations = rd_capture_open("evaluations");
  fprintf(rd_capture_evaluations, "rank,slot,stage,triangle_dt,vertex,id,destination,target_index,dMass,dMomentumX,dMomentumY,dEnergy\n");
}

static void rd_capture_element(tessellation *T, int triangle, int slot, int stage, double dt, double flux[4][3])
{
  if(!rd_capture_enabled)
    return;
  for(int j = 0; j < 3; j++)
    {
      const point *v = &T->DP[T->DT[triangle].p[j]];
      int index = v->originalindex;
      if(v->task == ThisTask)
        index = v->index >= NumGas ? v->index - NumGas : v->index;
      fprintf(rd_capture_evaluations, "%d,%d,%d,%.17g,%d,%llu,%d,%d,%.17g,%.17g,%.17g,%.17g\n",
              ThisTask, slot, stage, dt, j, (unsigned long long)v->ID, v->task, index,
              -dt * flux[0][j], -dt * flux[1][j], -dt * flux[2][j], -dt * flux[3][j]);
    }
}

static void rd_capture_exports(void)
{
  if(!rd_capture_enabled)
    return;
  fclose(rd_capture_evaluations);
  rd_capture_evaluations = NULL;
  FILE *fp = rd_capture_open("exports");
  fprintf(fp, "source,destination,target_index,dMass,dMomentumX,dMomentumY,dEnergy\n");
  for(int i = 0; i < N_FluxRD_export; i++)
    fprintf(fp, "%d,%d,%d,%.17g,%.17g,%.17g,%.17g\n", ThisTask, FluxRD_list[i].task,
            FluxRD_list[i].index, FluxRD_list[i].dMass_Dual, FluxRD_list[i].dMomentum_Dual[0],
            FluxRD_list[i].dMomentum_Dual[1], FluxRD_list[i].dEnergy_Dual);
  fclose(fp);
}

static void rd_capture_imports(const struct FluxRD_list_data *received)
{
  if(!rd_capture_enabled)
    return;
  FILE *fp = rd_capture_open("imports");
  fprintf(fp, "source,destination,target_index,id,dMass,dMomentumX,dMomentumY,dEnergy\n");
  for(int source = 0; source < NTask; source++)
    for(int j = 0; j < Recv_count[source]; j++)
      {
        int i = Recv_offset[source] + j;
        fprintf(fp, "%d,%d,%d,%llu,%.17g,%.17g,%.17g,%.17g\n", source, ThisTask, received[i].index,
                (unsigned long long)P[received[i].index].ID, received[i].dMass_Dual,
                received[i].dMomentum_Dual[0], received[i].dMomentum_Dual[1], received[i].dEnergy_Dual);
      }
  fclose(fp);
}
