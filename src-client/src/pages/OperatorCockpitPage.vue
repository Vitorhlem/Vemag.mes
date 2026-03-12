<template>
  <q-layout view="hHh lpR fFf" class="bg-grey-2 text-dark font-inter window-height overflow-hidden">
    
    <q-header bordered class="q-py-xs shadow-3 text-white" style="height: 65px; background-color: #008C7A;">
      <q-toolbar class="full-height q-px-md"> 
        
        <div class="row items-center no-wrap">
          <img :src="logoPath" alt="Logo" 
            :style="$q.screen.lt.md ? 'height: 30px' : 'height: 40px'" 
            style="max-width: 150px; object-fit: contain; filter: brightness(0) invert(1);" 
          />
          
          <q-separator vertical inset class="q-mx-md mobile-hide bg-white opacity-50" /> 
          
          <div class="column justify-center mobile-hide" style="max-width: 250px;">
            <div class="text-caption text-uppercase text-grey-3 letter-spacing-1 ellipsis" style="line-height: 1; font-size: 0.6rem;">
              {{ productionStore.machineSector }}
            </div>
            <div class="row items-center no-wrap q-mt-xs">
              <div class="text-h6 text-weight-bolder lh-small text-white q-mr-sm ellipsis">
                {{ productionStore.machineName }}
              </div>
              <q-badge rounded :class="statusBgClass" class="shadow-2 text-white q-py-xs q-px-sm text-caption no-wrap">
                <q-icon :name="statusIcon" color="white" class="q-mr-xs" size="14px" />
                {{ displayStatus }}
              </q-badge>
            </div>
          </div>
        </div>
        
        <q-space />
        
        <div class="row items-center q-gutter-x-sm q-mr-md">
          <q-badge :color="isOnline ? 'positive' : 'negative'" class="q-pa-xs shadow-1">
            <q-icon :name="isOnline ? 'wifi' : 'wifi_off'" size="14px" />
            <span class="q-ml-xs text-bold">{{ isOnline ? 'ONLINE' : 'OFFLINE' }}</span>
          </q-badge>

          <q-chip 
            v-if="pendingSyncCount > 0" 
            dense 
            color="orange-9" 
            text-color="white" 
            icon="sync" 
            class="animate-pulse"
          >
            {{ pendingSyncCount }} Pendentes
            <q-tooltip>Dados aguardando conexão para envio ao SAP</q-tooltip>
          </q-chip>
        </div>

        <div class="row items-center no-wrap q-gutter-x-sm">
          <div class="row items-center no-wrap bg-white text-dark q-py-xs q-px-sm rounded-borders shadow-2" style="height: 42px; border-radius: 10px;">
            <q-avatar size="28px" class="shadow-1 vemag-bg-primary text-white" icon="person" font-size="18px" />
            
            <div class="column items-start justify-center q-ml-sm mobile-hide" style="line-height: 1.1; max-width: 120px;">
              <div class="text-caption text-weight-bold vemag-text-primary text-uppercase" style="font-size: 0.55rem;">OPERADOR</div>
              <div class="text-caption text-grey-9 text-weight-bold ellipsis full-width">
                {{ productionStore.currentOperator?.full_name || productionStore.currentOperatorBadge || '---' }}
              </div>
            </div>
            
            <q-separator vertical inset class="q-mx-sm bg-grey-4" />
            
            <div class="text-h6 font-monospace vemag-text-primary text-weight-bold no-wrap" style="margin-top: 1px;">
              {{ timeDisplay }}
            </div>
          </div>
          
          <q-btn flat round icon="logout" class="text-white" size="md" padding="xs" @click="handleLogout">
              <q-tooltip>Sair do Sistema</q-tooltip>
          </q-btn>
        </div>

      </q-toolbar>
      <q-linear-progress :value="1" color="green" class="q-mt-none" size="4px" />
    </q-header>

    <q-page-container class="full-height">
      <q-page class="q-pa-sm full-height column no-wrap">
        
        <div v-if="!productionStore.activeOrder" class="col flex flex-center column">
          <q-card class="q-pa-lg text-center shadow-10 bg-white" style="border-radius: 20px; max-width: 500px; width: 90%;">
            <div class="vemag-bg-light q-pa-md rounded-borders inline-block q-mb-md">
               <q-icon name="qr_code_scanner" size="60px" class="vemag-text-primary" />
            </div>
            <div class="text-h4 text-weight-bolder vemag-text-primary q-mb-sm">Aguardando O.P.</div>
            <div class="text-subtitle1 text-grey-7 q-mb-lg">A máquina está parada.<br>Selecione uma opção:</div>
            
            <div class="column q-gutter-y-md">
                <q-btn push rounded color="blue-grey-9" text-color="white" class="full-width shadow-3" size="18px" padding="md" icon="list_alt" label="SELECIONAR DA LISTA" @click="openOpListDialog" />
                <div class="text-caption text-grey-5">- OU -</div>
                <q-btn push rounded class="vemag-bg-primary text-white full-width shadow-4" size="18px" padding="md" icon="photo_camera" label="LER QR CODE" @click="isCameraScannerOpen = true" />
            </div>
          </q-card>
        </div>

        <div v-else class="col column no-wrap q-gutter-y-sm content-stretch">
          
          <q-card class="col-auto q-px-md q-py-sm bg-white shadow-2 relative-position" style="border-radius: 12px; border-top: 5px solid #008C7A;">
            <div class="row items-center justify-between no-wrap">
                
                <div class="row items-center q-gutter-x-sm">
                    <q-badge 
                      :color="(productionStore.activeOrder.is_service || String(productionStore.activeOrder.code).startsWith('OS-')) ? 'blue-9' : 'orange-10'" 
                      :label="(productionStore.activeOrder.is_service || String(productionStore.activeOrder.code).startsWith('OS-')) ? 'SERVIÇO' : 'PRODUÇÃO'" 
                      class="text-bold shadow-1" 
                    />
                    
                    <div class="text-h6 text-weight-bolder text-primary ellipsis" style="max-width: 400px;">
                        {{ productionStore.activeOrder.part_name }}
                    </div>
                    
                    <div class="column q-ml-md" style="line-height: 1.2;">
                      <div class="text-subtitle1 text-weight-bold text-dark row items-baseline">
                        <span 
                          class="text-caption text-weight-bolder q-mr-xs" 
                          :class="(productionStore.activeOrder.is_service || String(productionStore.activeOrder.code).startsWith('OS-')) ? 'text-blue-9' : 'text-orange-9'"
                          style="font-size: 1em; letter-spacing: 1px;"
                        >
                          {{ (productionStore.activeOrder.is_service || String(productionStore.activeOrder.code).startsWith('OS-')) ? 'O.S:' : 'O.P:' }}
                        </span>
                        {{ 
                           (productionStore.activeOrder.is_service || String(productionStore.activeOrder.code).startsWith('OS-'))
                           ? (productionStore.activeOrder.code) 
                           : (productionStore.activeOrder.custom_ref || productionStore.activeOrder.code)
                        }}
                      </div>
                    </div>
                </div>

                <div class="row items-center q-gutter-x-lg">
                    
                    <div class="row items-center q-gutter-x-sm bg-grey-1 q-pa-xs rounded-borders" style="border: 1px solid #e0e0e0; min-width: 140px;">
                        <q-icon name="timer" :class="statusTextClass" size="26px" class="q-ml-xs" />
                        <div class="column q-mr-sm">
                            <div class="text-caption text-weight-bold text-grey-6" style="font-size: 0.6rem; line-height: 1;">TEMPO ATUAL</div>
                            <div class="text-h6 text-weight-bolder font-monospace" :class="statusTextClass" style="line-height: 1.1;">
                                {{ elapsedTime }}
                            </div>
                        </div>
                    </div>

                    <div class="row items-center q-gutter-x-md">
                      <div class="column items-end">
                          <div class="text-overline text-grey-7" style="line-height: 1;">META TOTAL</div>
                          <div class="text-subtitle1 text-weight-bold">
                              <span class="text-caption text-weight-bolder text-grey-8">{{ productionStore.activeOrder?.uom || 'pç' }}</span>
                          </div>
                      </div>
                      <q-circular-progress
                          show-value 
                          font-size="10px"
                          size="35px" 
                          :thickness="0.25" 
                          color="orange-8" 
                          track-color="grey-3" 
                          class="text-bold"
                      >
                      </q-circular-progress>
                    </div>

                </div>
            </div>
            <q-linear-progress stripe query :class="statusTextClass" size="4px" class="absolute-bottom" />
          </q-card>

          <q-card class="col column no-wrap overflow-hidden shadow-6 bg-white" style="border-radius: 12px; border-left: 10px solid #008C7A;">
            
            <div class="col-auto bg-grey-2 q-px-md q-py-xs border-bottom-light row items-center justify-between" v-if="productionStore.currentActiveStep">
              <div class="row items-center">
                  <template v-if="Number(productionStore.currentActiveStep.seq) === 999">
                    <q-badge color="red-10" text-color="white" class="q-mr-md q-py-xs q-px-sm shadow-2 text-bold">
                      <q-icon name="warning" size="14px" class="q-mr-xs" />
                      ETAPA FORA DO ROTEIRO (IMPREVISTA)
                    </q-badge>
                  </template>
                  <template v-else>
                    <div class="text-subtitle2 text-grey-7 q-mr-sm text-weight-bold">#{{ productionStore.currentActiveStep.seq }}</div>
                  </template>
                  
                  <div class="text-subtitle1 text-weight-bold ellipsis">{{ productionStore.currentActiveStep.name }}</div>
              </div>
              <q-chip square dense color="blue-grey-9" text-color="white" icon="precision_manufacturing" :label="productionStore.currentActiveStep.resource" class="text-caption" />
            </div>
            
            <div class="col scroll bg-white q-pa-md relative-position">
               <div class="row items-center q-mb-sm border-bottom-light q-pb-xs">
                  <q-icon name="menu_book" size="20px" class="text-primary q-mr-sm" /> 
                  <div class="text-subtitle2 text-weight-bold text-primary">INSTRUÇÕES DE TRABALHO</div>
               </div>
               
               <div 
                  class="text-grey-9 text-body1 q-mt-sm" 
                  style="line-height: 1.8;"
                  v-html="formatSapText(productionStore.currentActiveStep?.description)"
               >
               </div>
            </div>

            <q-separator />

            <q-card-actions class="col-auto q-pa-sm bg-grey-1 row items-center justify-between">
              <div class="row items-center q-gutter-x-md q-ml-sm">
                  <div class="column">
                    <div class="text-caption text-grey-7 text-uppercase text-weight-bold" style="font-size: 0.6rem; line-height: 1;">Tempo Estimado</div>
                    <div class="row items-center text-primary">
                        <q-icon name="timer" size="18px" class="q-mr-xs" />
                        <div class="text-h6 text-weight-bolder font-monospace">
                            {{ productionStore.currentActiveStep?.timeEst || 0 }}h
                        </div>
                    </div>
                  </div>
              </div>

              <div class="row items-center q-gutter-x-md">
                  
                  <q-btn 
                    push dense
                    color="red-10" 
                    text-color="white"
                    icon="campaign" 
                    label="CHAMAR AJUDA" 
                    class="q-px-md shadow-2 text-weight-bold"
                    @click="isAndonDialogOpen = true"
                  >
                      <q-tooltip>Abrir painel de notificação Andon</q-tooltip>
                  </q-btn>

                  <q-btn 
  v-if="productionStore.activeOrder?.drawing || productionStore.activeOrder?.item_code"
  push dense
  color="blue-grey-9" 
  text-color="white"
  icon="image" 
  label="VER DESENHO" 
  class="q-px-md shadow-2 text-weight-bold"
  @click="openDrawing"
>
  <q-tooltip>Visualizar Desenho Técnico</q-tooltip>
</q-btn>

              </div>
            </q-card-actions>
          </q-card>
        </div>
      </q-page>
    </q-page-container>

    <q-dialog v-model="showOpList" maximized transition-show="slide-up" transition-hide="slide-down">
  <q-card>
    <q-bar class="vemag-bg-primary text-white">
      <q-icon name="list" />
      <div class="text-h6 q-ml-sm">Ordens de Produção Liberadas (SAP)</div>
      <q-space />
      <q-btn dense flat icon="close" v-close-popup />
    </q-bar>
    
    <div class="bg-grey-2 q-pa-sm border-bottom-light row items-center">
      <q-input 
        v-model="searchQuery" 
        debounce="300" 
        outlined 
        dense 
        bg-color="white"
        placeholder="Pesquisar por O.P., Item ou Código..." 
        class="col-12 col-md-4"
        hide-bottom-space
      >
        <template v-slot:prepend>
          <q-icon name="search" color="teal-9" />
        </template>
        <template v-slot:append v-if="searchQuery">
            <q-icon name="close" @click="searchQuery = ''" class="cursor-pointer text-grey-6" />
        </template>
      </q-input>
      <q-space />
      <div class="text-caption text-grey-7 gt-sm">
        Use a barra para encontrar rapidamente a O.P. desejada.
      </div>
    </div>

    <q-card-section class="q-pa-none">
      <q-table 
        :rows="openOps" 
        :columns="opColumns" 
        row-key="op_number" 
        :loading="loadingOps" 
        flat 
        bordered 
        separator="cell"
        :filter="searchQuery"
        v-model:pagination="pagination"
        :rows-per-page-options="[10, 25, 50, 100, 0]"
      >
            <template v-slot:body="props">
              <q-tr 
                @click="(!props.row.steps || props.row.steps.length === 0) ? null : selectOp(props.row)" 
                :class="(!props.row.steps || props.row.steps.length === 0) ? 'bg-red-1 cursor-not-allowed opacity-70' : 'cursor-pointer hover-bg-grey-3'"
              >
                
                <q-td key="op_number" :props="props">
                  <template v-if="String(props.row.op_number).startsWith('OS-')">
                    <div class="text-weight-bold text-subtitle1 text-blue-9">{{ props.row.op_number }}</div>
                    <div class="text-caption text-grey-7">{{ props.row.custom_ref }}</div>
                  </template>

                  <template v-else>
                    <div class="text-weight-bold text-subtitle1 text-orange-9">{{ props.row.custom_ref || props.row.op_number }}</div>
                    <div v-if="props.row.custom_ref" class="text-caption text-grey-7">DocNum: {{ props.row.op_number }}</div>
                  </template>
                  
                  <q-badge v-if="!props.row.steps || props.row.steps.length === 0" color="negative" class="q-mt-xs text-weight-bold">
                    <q-icon name="warning" size="xs" class="q-mr-xs"/> Sem Roteiro / Operações
                  </q-badge>
                </q-td>

                <q-td key="part_name" :props="props">
                  <div class="text-body2 text-weight-medium">{{ props.row.part_name }}</div>
                </q-td>

                <q-td key="planned_qty" :props="props" class="text-center">
                  <q-badge color="teal-9" outline class="text-weight-bold" style="font-size: 0.85rem;">
                    {{ props.row.planned_qty }}
                  </q-badge>
                </q-td>

                <q-td key="action" :props="props" class="text-center">
                  <q-btn 
                    push 
                    color="teal-9" 
                    icon="play_arrow" 
                    label="Selecionar" 
                    size="sm"
                    class="text-weight-bold"
                    :disable="!props.row.steps || props.row.steps.length === 0"
                    @click.stop="selectOp(props.row)"
                  >
                    <q-tooltip v-if="!props.row.steps || props.row.steps.length === 0" class="bg-red-9">
                      Esta ordem não possui operações no SAP
                    </q-tooltip>
                  </q-btn>
                </q-td>
                
              </q-tr>
            </template>
        </q-table>
        </q-card-section>
      </q-card>
    </q-dialog>

    <q-dialog v-model="isShiftChangeDialogOpen" persistent>
      <q-card style="min-width: 350px">
        <q-card-section>
          <div class="text-h6 text-teal-9">Troca de Turno</div>
          <div class="text-subtitle2 text-grey-8">Como deseja prosseguir?</div>
        </q-card-section>

        <q-card-section class="q-pt-none">
          A máquina continuará produzindo durante a troca?
        </q-card-section>

        <q-card-actions align="right" class="text-primary">
          <q-btn flat label="Cancelar" v-close-popup color="grey" />
          <q-btn flat label="Não, Vai Parar" color="orange" @click="handleShiftChange(false)" />
          <q-btn push label="Sim, Continua Rodando" color="primary" icon="autorenew" @click="handleShiftChange(true)" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <q-dialog v-model="isDrawingDialogOpen" maximized transition-show="fade" transition-hide="fade">
      <q-card class="bg-grey-10 column fit relative-position overflow-hidden">
        
        <q-btn 
          round 
          color="red-10" 
          icon="close" 
          size="lg"
          class="absolute-top-right q-ma-lg z-top shadow-10" 
          v-close-popup 
        />

        <q-card-section class="col q-pa-none flex flex-center fit">
          <q-img 
            v-if="drawingUrl" 
            :src="drawingUrl" 
            class="fit" 
            fit="contain"
            spinner-color="teal-9"
            spinner-size="60px"
            @error="$q.notify({ type: 'negative', message: 'Falha ao carregar a imagem do servidor.', icon: 'broken_image' })"
          >
            <template v-slot:loading>
              <div class="text-teal-9 text-weight-bold q-mt-xl text-center">
                <q-icon name="manage_search" size="md" class="q-mb-sm block" />
                Buscando e renderizando desenho...<br>
                <span class="text-caption text-grey-6">(Pode levar alguns segundos na primeira vez)</span>
              </div>
            </template>
            
            <template v-slot:error>
              <div class="absolute-full flex flex-center bg-grey-9 text-white column">
                <q-icon name="broken_image" size="60px" color="grey-6" />
                <div class="text-h6 q-mt-md">Desenho indisponível</div>
                <div class="text-body2 text-grey-5">O arquivo não foi encontrado na engenharia.</div>
              </div>
            </template>
          </q-img>
        </q-card-section>
        
      </q-card>
    </q-dialog>

    <q-dialog v-model="isStopDialogOpen" persistent maximized transition-show="slide-up" transition-hide="slide-down">
      
      <q-card class="column" :class="stopDialogAlertActive ? 'critical-alert-flash' : 'bg-grey-2'">
        
        <q-toolbar class="text-dark q-py-md shadow-2 z-top" :class="stopDialogAlertActive ? 'bg-red-10 text-white' : 'bg-white'">
          <q-toolbar-title class="text-weight-bold text-h6 row items-center">
            <q-icon name="warning" :color="stopDialogAlertActive ? 'white' : 'warning'" size="30px" class="q-mr-md"/> 
            {{ stopDialogAlertActive ? 'SELECIONE O MOTIVO IMEDIATAMENTE!' : 'SELECIONE O MOTIVO' }}
          </q-toolbar-title>
          <q-btn flat round icon="close" size="lg" v-close-popup />
        </q-toolbar>

        <div class="q-pa-md bg-white border-bottom-light">
            <q-banner rounded class="bg-red-1 text-center q-mb-sm shadow-1">
                <template v-slot:avatar>
                    <q-icon name="help_outline" color="red-10" />
                </template>
                <div class="text-subtitle1 text-red-10 text-weight-bold">O trabalho nesta etapa terminou?</div>
            </q-banner>
            
            <q-btn 
                push 
                color="red-10" 
                text-color="white" 
                class="full-width shadow-3" 
                size="lg" 
                padding="md"
                @click="confirmFinishOp"
            >
                <div class="row items-center justify-center full-width">
                    <span class="text-weight-bolder q-mr-md">ENCERRAR ETAPA</span>
                    <q-icon name="stop_circle" size="32px" />
                </div>
            </q-btn>
        </div>

        <q-card-section class="col column q-pa-none">
            <div class="q-pa-md">
                <q-input v-model="stopSearch" outlined bg-color="white" placeholder="Pesquisar motivo de parada..." dense autofocus clearable />
            </div>
            
            <div class="col scroll q-px-md q-pb-md">
               <div class="row q-col-gutter-md">
                  <div v-for="(reason, idx) in filteredStopReasons" :key="idx" class="col-12 col-sm-6 col-md-4">
                    <q-btn 
                        flat bordered 
                        class="full-width reason-card" 
                        :class="{ 
                          'highlight-shift': reason.code === '111', 
                          'highlight-maintenance': reason.requiresMaintenance,
                          'highlight-setup': reason.code === '52'
                        }"
                        @click="handleSapPause(reason)"
                        :disable="reason.code === '111'"
                    >
                        <div class="row items-center no-wrap full-width q-pa-sm">
                          <q-avatar 
                            size="48px" 
                            :color="reason.code === '111' ? 'orange-9' : (reason.requiresMaintenance ? 'red-10' : (reason.code === '52' ? 'purple-9' : 'grey-3'))" 
                            :text-color="reason.code === '111' || reason.requiresMaintenance || reason.code === '52' ? 'white' : 'grey-9'"
                            :class="{ 'pulse-animation': reason.code === '111' || reason.requiresMaintenance || reason.code === '52' }"
                          >
                            <q-icon 
                              :name="reason.code === '111' ? 'groups' : (reason.requiresMaintenance ? 'engineering' : (reason.code === '52' ? 'build_circle' : 'pause'))" 
                              size="28px" 
                            />
                          </q-avatar>

                          <div class="column q-ml-md text-left">
                            <div 
                              class="text-subtitle1 text-weight-bolder" 
                              :class="{ 
                                'text-orange-10': reason.code === '111', 
                                'text-red-10': reason.requiresMaintenance,
                                'text-purple-10': reason.code === '52'
                              }"
                            >
                              {{ reason.label.toUpperCase() }}
                            </div>
                            <div v-if="reason.isSpecial || reason.code === '52'" class="text-caption text-grey-6" style="line-height: 1;">
                                {{ reason.code === '111' ? 'Temporariamente Inativo' : 'Ação Prioritária' }}
                            </div>
                          </div>
                        </div>
                    </q-btn>
                  </div>
               </div>
            </div>
        </q-card-section>
      </q-card>
    </q-dialog>

    <q-dialog v-model="isAndonDialogOpen" transition-show="scale" transition-hide="scale">
      <q-card style="width: 800px; max-width: 95vw; border-radius: 20px;">
        
        <q-card-section class="vemag-bg-primary text-white row items-center justify-between q-pa-md">
          <div class="text-h6 text-weight-bold row items-center">
            <q-icon name="campaign" size="30px" class="q-mr-sm" /> 
            Central de Ajuda (Andon)
          </div>
          <q-btn icon="close" flat round size="md" v-close-popup />
        </q-card-section>

        <q-card-section class="q-pt-md q-px-lg">
            <div class="text-subtitle2 text-grey-7 q-mb-xs">Observação / Detalhe do Problema (Opcional):</div>
            <q-input 
              v-model="andonNote" 
              outlined 
              type="textarea" 
              rows="2"
              placeholder="Ex: Falta parafuso M8..." 
              bg-color="grey-1"
              class="text-h6"
            />
        </q-card-section>

        <q-separator inset />

        <q-card-section class="q-pa-lg">
          <div class="text-subtitle2 text-center text-grey-8 q-mb-md text-uppercase">Selecione o setor para chamar:</div>
          
          <div class="row q-col-gutter-md">
            <div v-for="opt in andonOptions" :key="opt.label" class="col-6 col-md-3">
              <q-btn 
                push 
                class="full-width full-height column flex-center q-pa-sm shadow-3 hover-scale" 
                :class="`bg-${opt.color} text-white`" 
                style="border-radius: 16px; min-height: 90px;" 
                @click="confirmAndonCall(opt.label)"
              >
                <q-icon :name="opt.icon" size="32px" class="q-mb-xs" />
                <div class="text-subtitle2 text-weight-bold" style="line-height: 1.1;">{{ opt.label }}</div>
              </q-btn>
            </div>
          </div>
        </q-card-section>
      </q-card>
    </q-dialog>
    <q-dialog v-model="isStepConfirmationDialogOpen" persistent>
      <q-card style="min-width: 450px; border-radius: 16px;">
        <q-card-section class="vemag-bg-primary text-white row items-center">
          <div class="text-h6 row items-center">
            <q-icon name="route" size="sm" class="q-mr-sm" /> Confirmação de Etapa
          </div>
        </q-card-section>

        <q-card-section class="q-pt-md">
          <div class="text-subtitle1 text-weight-bold text-grey-8 q-mb-sm text-center">
            A melhor operação identificada para esta máquina é:
          </div>

          <q-card flat bordered class="bg-teal-1 q-pa-sm q-mb-md" style="border-color: #008C7A;">
            <div class="row items-center no-wrap">
              <q-avatar color="teal-9" text-color="white" class="text-weight-bold q-mr-md shadow-2">
                {{ suggestedStep?.seq === 999 ? '!' : suggestedStep?.seq || '--' }}
              </q-avatar>
              <div class="column col">
                <div class="text-subtitle1 text-weight-bolder text-teal-10" style="line-height: 1.2;">
                  {{ suggestedStep?.name || 'Operação' }}
                </div>
                <div class="text-caption text-teal-8 text-weight-bold q-mt-xs">
                  Recurso: {{ suggestedStep?.resource || '---' }}
                </div>
              </div>
            </div>
          </q-card>

          <div class="text-h6 text-center text-dark q-mt-md">
            Deseja trabalhar em outra etapa?
          </div>
        </q-card-section>

        <q-card-actions align="center" class="q-pb-lg q-px-md column q-gutter-y-sm">
          <q-btn
            push
            label="NÃO, INICIAR ESTA ETAPA"
            color="teal-9"
            class="full-width text-weight-bold shadow-3"
            size="lg"
            icon="play_arrow"
            @click="confirmAndStartStep"
          />
          <q-btn
            outline
            label="SIM, ESCOLHER DA LISTA"
            color="orange-9"
            class="full-width text-weight-bold bg-orange-1"
            size="md"
            icon="list"
            @click="openStepSelection"
          />
          <q-btn
            flat
            label="Cancelar e Voltar"
            color="grey-7"
            class="full-width q-mt-sm"
            @click="cancelStepSelection"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <q-dialog v-model="isStepSelectionDialogOpen" maximized transition-show="slide-up" transition-hide="slide-down">
      <q-card class="bg-grey-2 column">
        <q-bar class="vemag-bg-primary text-white" style="height: 60px;">
          <q-icon name="list_alt" size="24px" />
          <div class="text-h6 q-ml-sm">Selecione a Etapa para Trabalhar</div>
          <q-space />
          <q-btn dense flat icon="close" size="20px" @click="cancelStepSelection" />
        </q-bar>

        <q-card-section class="col scroll q-pa-md">
          <div class="text-subtitle1 text-grey-8 q-mb-md">
            Selecione a operação que deseja iniciar na <b>{{ productionStore.activeOrder?.code }}</b>:
          </div>

          <div class="row q-col-gutter-md">
            <div v-for="(step, index) in productionStore.activeOrder?.steps" :key="index" class="col-12 col-md-6 col-lg-4">
              <q-card
                class="cursor-pointer hover-scale transition-all"
                :class="index === productionStore.currentStepIndex ? 'bg-teal-1 shadow-4' : 'bg-white shadow-2'"
                style="border-radius: 12px; border: 2px solid transparent;"
                :style="index === productionStore.currentStepIndex ? 'border-color: #008C7A;' : ''"
                @click="selectManualStep(index)"
              >
                <q-card-section class="row items-center no-wrap">
                  <q-avatar
                    :color="index === productionStore.currentStepIndex ? 'teal-9' : 'blue-grey-8'"
                    text-color="white"
                    class="q-mr-md shadow-2 text-weight-bold"
                  >
                    {{ step.seq === 999 ? '!' : step.seq }}
                  </q-avatar>
                  <div class="column col">
                    <div class="text-subtitle1 text-weight-bold ellipsis" :class="index === productionStore.currentStepIndex ? 'text-teal-10' : 'text-dark'">
                      {{ step.name }}
                    </div>
                    <div class="row items-center justify-between q-mt-xs">
                       <q-badge :color="index === productionStore.currentStepIndex ? 'teal-7' : 'grey-6'">
                          {{ step.resource }}
                       </q-badge>
                       <div class="text-caption text-grey-7 text-weight-bold row items-center">
                          <q-icon name="timer" class="q-mr-xs"/> {{ step.timeEst || 0 }}h
                       </div>
                    </div>
                  </div>
                  <q-icon
                    v-if="index === productionStore.currentStepIndex"
                    name="star"
                    color="orange-6"
                    size="sm"
                    class="absolute-top-right q-pa-sm"
                  >
                    <q-tooltip>Recomendada para esta máquina</q-tooltip>
                  </q-icon>
                </q-card-section>
              </q-card>
            </div>
          </div>
        </q-card-section>
      </q-card>
    </q-dialog>
    <q-dialog v-model="isCameraScannerOpen" maximized transition-show="fade" transition-hide="fade">
      <q-card class="bg-black text-white column">
        <q-bar class="bg-grey-10 q-pa-sm" style="height: 60px; z-index: 10;">
          <q-icon name="qr_code_scanner" size="24px" />
          <div class="text-h6 q-ml-md">Escaneie a Ordem ou Crachá</div>
          <q-space />
          <q-btn dense flat icon="close" size="20px" v-close-popup />
        </q-bar>

        <q-card-section class="col flex flex-center q-pa-none relative-position bg-black">
          <qrcode-stream 
            @detect="onDetectCode" 
            :track="paintOutline"
            @error="onCameraError"
          ></qrcode-stream>
          
          <div class="absolute-bottom text-center q-pb-xl text-grey-4">
            Aponte a câmera para o QR Code da O.P. ou do seu crachá
          </div>
        </q-card-section>
      </q-card>
    </q-dialog>

  </q-layout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { Notify, useQuasar } from 'quasar';
import { useProductionStore } from 'stores/production-store';
import { storeToRefs } from 'pinia';
import { ProductionService } from 'src/services/production-service';
import { useAuthStore } from 'stores/auth-store';
import { api } from 'boot/axios'; 
import { db } from 'src/db/offline-db';
import { QrcodeStream } from 'vue-qrcode-reader';
import { getOperatorName } from 'src/data/operators'; 
import { SAP_OPERATIONS_MAP } from 'src/data/sap-operations';
import { SAP_STOP_REASONS } from 'src/data/sap-stops';
import { ANDON_OPTIONS } from 'src/data/andon-options';
const isStepConfirmationDialogOpen = ref(false);
const isStepSelectionDialogOpen = ref(false);

const suggestedStep = computed(() => {
    if (!productionStore.activeOrder?.steps || productionStore.activeOrder.steps.length === 0) return null;
    const index = productionStore.currentStepIndex !== -1 ? productionStore.currentStepIndex : 0;
    return productionStore.activeOrder.steps[index];
});
const isSocketConnected = ref(false);
const router = useRouter();
const $q = useQuasar();
const searchQuery = ref('');
const pagination = ref({
  sortBy: 'op_number',
  descending: true,  
  page: 1,
  rowsPerPage: 50     
});
const productionStore = useProductionStore();
const authStore = useAuthStore();
const { activeOrder } = storeToRefs(productionStore); 
const isShiftChangeDialogOpen = ref(false);
const logoPath = ref('/WhiteLogo.png');
const opNumberToSend = computed(() => {
  if (!productionStore.activeOrder) return '';
  const order = productionStore.activeOrder;
  
  const codeStr = String(order.code || '').trim();
  const customRef = String(order.custom_ref || '').trim();
  const opNum = String(order.op_number || '').trim();

  // 1. É ORDEM DE SERVIÇO?
  if (order.is_service || codeStr.startsWith('OS-')) {
     if (!codeStr.startsWith('OS-')) return `OS-${codeStr}`;
     return codeStr; 
  }

  // 2. É ORDEM DE PRODUÇÃO (O.P.)
  if (customRef.toUpperCase().includes('CLIENTE:')) {
     return opNum || codeStr;
  }

  return customRef || opNum || codeStr;
});
const isPaused = ref(false);
const currentPauseObj = ref<{
  startTime: Date;
  reasonCode: string;
  reasonLabel: string;
} | null>(null);

const isStopDialogOpen = ref(false);
const isAndonDialogOpen = ref(false);
const isDrawingDialogOpen = ref(false);
const drawingUrl = ref('');
function openDrawing() {
    const rawCode = productionStore.activeOrder?.drawing || productionStore.activeOrder?.item_code;
    
    if (!rawCode || String(rawCode).trim() === '') {
        $q.notify({ type: 'warning', message: 'Nenhum código encontrado.', icon: 'warning' });
        return;
    }

    const codigoBusca = String(rawCode).trim();

    // 1. Abre a tela preta com a mensagem de "Buscando e renderizando..." e limpa a imagem velha
    isDrawingDialogOpen.value = true;
    drawingUrl.value = ''; 

    if (codigoBusca.startsWith('http')) {
        drawingUrl.value = codigoBusca;
        return;
    }

    // 2. Avisa o FastAPI para ligar o Celery
    api.post(`/drawings/request/${encodeURIComponent(codigoBusca)}/${productionStore.machineId}`)
       .then(() => console.log("Ordem enviada ao Celery! Aguardando o WebSocket..."))
       .catch(e => {
           isDrawingDialogOpen.value = false;
           $q.notify({ type: 'negative', message: 'Erro ao comunicar com o servidor.' });
       });
}
const showOpList = ref(false);
const loadingOps = ref(false);

const stopSearch = ref('');
const statusStartTime = ref(new Date());
const currentTime = ref(new Date());
let timerInterval: ReturnType<typeof setInterval>;
const andonNote = ref('');

const andonOptions = ANDON_OPTIONS; 


const openOps = ref([]);
const opColumns = [
  { name: 'op_number', label: 'Nome / Identificação', align: 'left', field: 'op_number', sortable: true },
  { name: 'part_name', label: 'Produto / Item', align: 'left', field: 'part_name', sortable: true },
  { name: 'planned_qty', label: 'Qtd', align: 'center', field: 'planned_qty' },
  { name: 'action', label: 'Selecionar', align: 'center' }
];

const viewedStepIndex = ref(0);

const currentViewedStep = computed(() => {
    if (activeOrder.value?.steps && activeOrder.value.steps.length > 0) {
        return activeOrder.value.steps[viewedStepIndex.value];
    }
    return { 
        seq: '---', 
        name: 'Aguardando Roteiro', 
        description: 'Buscando operações no SAP...', 
        resource: '---', 
        timeEst: 0 
    };
});

const isOnline = ref(window.navigator.onLine);

const isCameraScannerOpen = ref(false);

// FUNÇÃO PARA DESENHAR UM QUADRADO VERDE EM VOLTA DO QR CODE NA TELA
function paintOutline(detectedCodes: any, ctx: CanvasRenderingContext2D) {
  for (const detectedCode of detectedCodes) {
    const [firstPoint, ...otherPoints] = detectedCode.cornerPoints;

    ctx.strokeStyle = '#008C7A'; // Cor do sistema
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.moveTo(firstPoint.x, firstPoint.y);
    for (const { x, y } of otherPoints) {
      ctx.lineTo(x, y);
    }
    ctx.lineTo(firstPoint.x, firstPoint.y);
    ctx.closePath();
    ctx.stroke();
  }
}

// FUNÇÃO QUE RODA ASSIM QUE A CÂMERA LÊ O QR CODE
async function onDetectCode(detectedCodes: any[]) {
  if (detectedCodes.length > 0) {
    const scannedText = detectedCodes[0].rawValue.trim();
    
    // 1. Fecha a câmera e faz um som de "Bip" sucesso
    isCameraScannerOpen.value = false;
    playBeep(); 

    // 2. Inteligência: Decide se é OP ou Crachá (Mesma lógica do leitor USB)
    const isOperatorLoggedIn = !!productionStore.currentOperatorBadge || !!authStore.user;

    if (isOperatorLoggedIn && !productionStore.activeOrder) {
      // ESTÁ LOGADO -> ENTÃO É UMA O.P.
      $q.loading.show({
          message: `Buscando Ordem ${scannedText} no SAP...`,
          spinnerColor: 'teal-9',
          customClass: 'text-weight-bold text-h6'
      });

      try {
          await productionStore.requestOrderFromSAP(scannedText);
      } catch (e) {
          console.error(e);
          $q.notify({ type: 'negative', message: 'Ordem não encontrada no SAP.' });
      }
    } else {
      // NÃO ESTÁ LOGADO -> ENTÃO É UM CRACHÁ
      $q.loading.show({ message: `Autenticando crachá...` });
      try {
        await authStore.loginByBadge(scannedText);
        if (authStore.user?.employee_id) {
          productionStore.currentOperatorBadge = authStore.user.employee_id;
          $q.notify({ type: 'positive', message: `Olá, ${authStore.user.full_name}`, icon: 'person' });
        } else {
          productionStore.currentOperatorBadge = scannedText;
        }
      } catch (e) {
        console.error("Erro ao ler crachá:", e);
        $q.notify({ type: 'negative', message: 'Crachá não reconhecido.' });
      } finally {
        $q.loading.hide();
      }
    }
  }
}

// TRATAMENTO DE ERROS DE PERMISSÃO DA CÂMERA
function onCameraError(error: any) {
  console.error(error);
  let errorMessage = "Erro desconhecido ao abrir a câmera.";
  
  if (error.name === 'NotAllowedError') errorMessage = "Permissão da câmera negada.";
  else if (error.name === 'NotFoundError') errorMessage = "Nenhuma câmera encontrada no tablet.";
  else if (error.name === 'NotSupportedError') errorMessage = "É necessário HTTPS para usar a câmera.";

  $q.notify({ type: 'negative', message: errorMessage, icon: 'warning' });
  isCameraScannerOpen.value = false;
}

function openStepSelection() {
    isStepConfirmationDialogOpen.value = false;
    isStepSelectionDialogOpen.value = true;
}

function cancelStepSelection() {
    isStepConfirmationDialogOpen.value = false;
    isStepSelectionDialogOpen.value = false;
    productionStore.activeOrder = null; 
    $q.loading.hide();
}

function selectManualStep(index: number) {
    productionStore.currentStepIndex = index;
    viewedStepIndex.value = index;
    confirmAndStartStep();
}

function confirmAndStartStep() {
    isStepConfirmationDialogOpen.value = false;
    isStepSelectionDialogOpen.value = false;

    if (productionStore.currentMachine) {
        productionStore.currentMachine.status = 'SETUP';
    }
    productionStore.isInSetup = true;
    isPaused.value = false;

    if (productionStore.currentStepIndex !== -1) {
         viewedStepIndex.value = productionStore.currentStepIndex;
    }
    resetTimer();

    $q.notify({
        type: 'positive',
        message: `Etapa ${suggestedStep.value?.seq || ''} iniciada com sucesso.`,
        icon: 'play_arrow'
    });
}

function formatSapText(text: string | undefined | null) {
  if (!text) return 'Nenhuma instrução disponível para esta etapa.';
  
  let formatted = String(text);

  formatted = formatted.replace(/\\r\\n/g, '<br>')
                       .replace(/\\n/g, '<br>')
                       .replace(/\r\n/g, '<br>')
                       .replace(/\n/g, '<br>');


  // eslint-disable-next-line no-useless-escape
  formatted = formatted.replace(/\.\-\s/g, '.<br><br>• ');
  // eslint-disable-next-line no-useless-escape
  formatted = formatted.replace(/(?<!^)\s\-\s/g, '<br> - ');

  return formatted;
}

async function checkSyncQueue() {
  pendingSyncCount.value = await db.sync_queue.where('status').equals('pending').count();
  
  if (isOnline.value && pendingSyncCount.value > 0) {
    const items = await db.sync_queue.where('status').equals('pending').toArray();
    try {
      await api.post('/production/sync-batch', items);
      await db.sync_queue.clear(); 
      pendingSyncCount.value = 0;
      $q.notify({ type: 'positive', message: 'Sincronização concluída com sucesso!' });
    } catch (e) {
      console.error('Falha ao sincronizar lote', e);
    }
  }
}

window.addEventListener('online', () => { isOnline.value = true; void checkSyncQueue(); });
window.addEventListener('offline', () => { isOnline.value = false; });

const elapsedTime = computed(() => {
   const diff = Math.max(0, Math.floor((currentTime.value.getTime() - statusStartTime.value.getTime()) / 1000));
   const h = Math.floor(diff / 3600).toString().padStart(2, '0');
   const m = Math.floor((diff % 3600) / 60).toString().padStart(2, '0');
   const s = (diff % 60).toString().padStart(2, '0');
   return `${h}:${m}:${s}`;
});
const timeDisplay = computed(() => currentTime.value.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }));

const normalizedStatus = computed(() => {
  const s = String(productionStore.currentMachine?.status || '').toUpperCase();

  if (s.includes('USO') || s.includes('RUNNING') || s.includes('OPERAÇÃO') || s.includes('PRODUCING')) return 'EM OPERAÇÃO';
  if (s.includes('AUTÔNOM') || s.includes('AUTONOMOUS')) return 'AUTÔNOMO';
  if (s.includes('SETUP') || s.includes('PREPARA')) return 'SETUP';
  if (s.includes('MANUTEN') || s.includes('MAINTENANCE')) return 'MANUTENÇÃO';
  if (s.includes('PARADA') || s.includes('PAUS') || s.includes('STOPPED')) return 'PARADA';
  if (s.includes('OCIOS') || s.includes('DISPON') || s.includes('IDLE')) return 'OCIOSO';

  return 'DISPONÍVEL';
});
const displayStatus = computed(() => {
  if (isPaused.value) return 'PAUSADA - ' + (currentPauseObj.value?.reasonLabel || '');
  
  return normalizedStatus.value;
});
const statusBgClass = computed(() => {
  const s = normalizedStatus.value;
  if (s === 'SETUP') return 'bg-purple-9 text-white';
  if (s === 'MANUTENÇÃO') return 'bg-red-10 text-white';
  if (s === 'AUTÔNOMO') return 'bg-blue-6 text-white'; 
  if (s === 'EM OPERAÇÃO') return 'bg-positive text-white';
  if (s === 'PARADA') return 'bg-orange-9 text-white';
  if (s === 'OCIOSO') return 'bg-grey-7 text-white';
  
  return 'bg-blue-grey-9 text-white';
});

const statusTextClass = computed(() => {
  const s = normalizedStatus.value;
  if (s === 'EM OPERAÇÃO' || s === 'AUTÔNOMO') return 'vemag-text-primary';
  if (s === 'SETUP') return 'text-purple-9';
  if (s === 'MANUTENÇÃO') return 'text-red-10';
  return 'text-grey-8';
});

const statusIcon = computed(() => {
  const s = normalizedStatus.value;
  if (s === 'SETUP') return 'build_circle';
  if (s === 'MANUTENÇÃO') return 'engineering';
  if (s === 'AUTÔNOMO') return 'smart_toy'; 
  if (s === 'EM OPERAÇÃO') return 'autorenew';
  if (s === 'PARADA') return 'pause_circle_filled';
  return 'hourglass_empty';
});



const filteredStopReasons = computed(() => {
   if (!stopSearch.value) return SAP_STOP_REASONS;
   const needle = stopSearch.value.toLowerCase();
   return SAP_STOP_REASONS.filter(r => r.label.toLowerCase().includes(needle));
});


function resetTimer() { statusStartTime.value = new Date(); }

const pendingSyncCount = ref(0);
const isSyncing = ref(false);

async function syncOfflineData() {
  if (!isOnline.value || isSyncing.value) return;

  pendingSyncCount.value = await db.sync_queue.where('status').equals('pending').count();
  
  if (pendingSyncCount.value === 0) return;

  try {
    isSyncing.value = true;
    
    const items = await db.sync_queue.where('status').equals('pending').toArray();
    
    await api.post('/production/sync-batch', items);

    await db.sync_queue.where('status').equals('pending').delete();
    
    pendingSyncCount.value = 0;
    
    Notify.create({ 
      type: 'positive', 
      icon: 'cloud_done',
      message: 'Sincronização concluída!',
      caption: `${items.length} apontamentos enviados ao SAP.`,
      position: 'top'
    });

  } catch (error) {
    console.error('Falha na sincronização de lote:', error);
    Notify.create({ 
      type: 'negative', 
      message: 'Erro ao sincronizar dados offline. Tentaremos novamente em breve.' 
    });
  } finally {
    isSyncing.value = false;
  }
}

const updateOnlineStatus = () => {
  const status = window.navigator.onLine;
  isOnline.value = status;
  
  if (status) {
    void syncOfflineData();
  } else {
    Notify.create({ 
      group: 'network', 
      type: 'warning', 
      icon: 'cloud_off',
      message: 'Você está Offline. O sistema continuará salvando seus dados localmente.',
      timeout: 0, 
      actions: [{ label: 'Entendi', color: 'white' }]
    });
  }
};

async function openOpListDialog() {
  showOpList.value = true;
  loadingOps.value = true;
  openOps.value = []; 
  searchQuery.value = ''; 
  
  try {
    await api.get(`/production/orders/open?machine_id=${productionStore.machineId}`);
  } catch (error) {
    console.error(error);
    $q.notify({ type: 'negative', message: 'Erro ao solicitar OPs' });
    loadingOps.value = false;
  }
}
// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function selectOp(op: any) {
  if (!op.steps || op.steps.length === 0) {
      $q.notify({ 
          type: 'negative', 
          message: 'Esta O.P. não possui operações/roteiro cadastrado no SAP.',
          icon: 'block' 
      });
      return;
  }

  showOpList.value = false;
  

  $q.loading.show({
      message: 'Carregando melhor operação...',
      spinnerColor: 'teal-9',
      customClass: 'text-weight-bold text-h6'
  });

  await productionStore.requestOrderFromSAP(String(op.op_number));
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function handleSapPause(stopReason: any) {
  console.log(`🛑 [UI] Motivo Selecionado: ${stopReason.label} (${stopReason.code})`);

  // 1. Atualiza o objeto local
  if (!currentPauseObj.value) {
      currentPauseObj.value = { 
          startTime: new Date(), 
          reasonCode: stopReason.code, 
          reasonLabel: stopReason.label 
      };
  } else {
      currentPauseObj.value.reasonCode = stopReason.code;
      currentPauseObj.value.reasonLabel = stopReason.label;
  }

  try {
      await productionStore.sendEvent('STATUS_CHANGE', { 
          new_status: 'STOPPED', 
          reason: stopReason.label 
      });
  } catch (e) {
      console.error("Erro ao atualizar motivo no backend:", e);
  }

  isStopDialogOpen.value = false;

  // --- TRATAMENTO DE CASOS ESPECIAIS ---

  if (stopReason.code === '52') {
      void productionStore.setMachineStatus('SETUP');
      void productionStore.sendEvent('STATUS_CHANGE', { new_status: 'SETUP', reason: 'Preparação / Setup' });
      productionStore.isInSetup = true; 
      $q.notify({ type: 'info', color: 'purple-9', icon: 'build_circle', message: 'Modo Setup Ativado.' });
      return;
  }


  if (stopReason.code === '21' || stopReason.requiresMaintenance) {
      void triggerCriticalBreakdown(); 
      return;
  }


  if (stopReason.code === '111') {
      isShiftChangeDialogOpen.value = true; 
      return;
  }

  $q.notify({ type: 'info', message: `Motivo registrado: ${stopReason.label}`, icon: 'timer' });
}
async function applyNormalPause(fromPlc = false) {
  console.log("%c🛑 INICIANDO PROCESSO DE PAUSA...", "color: orange; font-weight: bold; font-size: 14px");

  const currentOrder = productionStore.activeOrder;
  const currentBadge = productionStore.activeOperator?.badge || productionStore.currentOperatorBadge;
  const now = new Date();
  const codeToSend = opNumberToSend.value;

  if (!currentOrder || !codeToSend) {
      console.warn("⚠️ Sem ordem ativa ou código inválido. Pulando apontamento de produção.");
      isPaused.value = true;
      if (productionStore.currentMachine) productionStore.currentMachine.status = 'Parada';
      isStopDialogOpen.value = true;
      return;
  }

  if (!currentPauseObj.value) {
    currentPauseObj.value = { startTime: now, reasonCode: '0', reasonLabel: 'SEM MOTIVO' };
  }

  isPaused.value = true;
  $q.loading.show({ message: 'Encerrando ciclo de produção...' });

  try {
    const machineRes = productionStore.machineResource;
    const actualStep = currentViewedStep.value;
    const prodStart = statusStartTime.value ? new Date(statusStartTime.value) : new Date();
    const rawSeq = Number(actualStep?.seq || 10);
    const position = rawSeq === 999 ? '999' : rawSeq.toString().padStart(3, '0');
    
    let sapData = actualStep && actualStep.resource ? SAP_OPERATIONS_MAP[actualStep.resource] : null;
    
    if (!sapData) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        sapData = Object.values(SAP_OPERATIONS_MAP).find((op: any) => op.resourceCode === machineRes) || { code: '', description: '' };
    }

    const productionPayload = {
        op_number: String(codeToSend), 
        position: position, 
        operation: sapData.code || '', 
        operation_desc: actualStep?.name || sapData.description || '', 
        part_description: currentOrder.part_name || '', 
        item_code: currentOrder.item_code || currentOrder.part_code || '', 
        resource_code: machineRes || '4.02.01',
        resource_name: productionStore.machineName || 'Máquina',
        operator_id: String(currentBadge || '0'),
        operator_name: getOperatorName(String(currentBadge || '')),
        machine_id: productionStore.machineId,
        start_time: prodStart.toISOString(),
        end_time: now.toISOString(),
        stop_reason: '', 
        DataSource: 'I',
        U_TipoDocumento: '1' 
    };

    console.log("🚀 Enviando Payload de Produção:", productionPayload);

    try {
        const resp = await ProductionService.sendAppointment(productionPayload);
        console.log("✅ Produção registrada com sucesso!", resp);
    } catch (innerError) {
        console.error("❌ Erro ao enviar produção:", innerError);
        $q.notify({ type: 'warning', message: 'Aviso: Falha ao registrar tempo de produção.' });
    }

    if (activeOrder.value) activeOrder.value.status = 'PAUSED';
    if (productionStore.currentMachine) productionStore.currentMachine.status = 'Parada';

    if (!fromPlc) {
      await productionStore.setMachineStatus('STOPPED');
      await productionStore.sendEvent('STATUS_CHANGE', { 
          new_status: 'STOPPED', 
          reason: currentPauseObj.value.reasonLabel 
      });
    }

    statusStartTime.value = new Date(); 
    isStopDialogOpen.value = true;

  } catch (error) {
    console.error("🔥 ERRO CRÍTICO NA PAUSA:", error);
    isPaused.value = false; 
  } finally {
    $q.loading.hide();
  }
}


async function triggerCriticalBreakdown() {
    if (!currentPauseObj.value) return;
    
    $q.loading.show({ 
        message: '🚨 Registrando Manutenção no SAP...', 
        backgroundColor: 'red-10'
    });

    try {
        const now = new Date();
        const productionStart = statusStartTime.value;
        const eventTime = now.toISOString();
        
        let badge = productionStore.activeOperator.badge || productionStore.currentOperatorBadge;
        if (!badge && authStore.user?.employee_id && authStore.user.role !== 'admin') {
             badge = authStore.user.employee_id;
        }
        const operatorName = getOperatorName(String(badge).trim());
        const machineRes = productionStore.machineResource || '4.02.01';
        const machineName = productionStore.machineName || '';

        if (activeOrder.value?.code) {
            
            const actualStep = currentViewedStep.value;

            const rawSeq = Number(actualStep?.seq || 10);
            const stageStr = rawSeq === 999 ? '999' : rawSeq.toString().padStart(3, '0');
            
            let sapData = actualStep && actualStep.resource ? SAP_OPERATIONS_MAP[actualStep.resource] : null;
            if (!sapData) {
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
                sapData = Object.values(SAP_OPERATIONS_MAP).find((op: any) => op.resourceCode === machineRes) || { code: '', description: '' };
            }

            const productionPayload = {
                op_number: String(opNumberToSend.value),
                position: stageStr,
                operation: sapData.code || '',        
                operation_desc: actualStep?.name || sapData.description || '', 
                part_description: activeOrder.value.part_name || '',
                resource_code: machineRes,
                resource_name: machineName,            
                operator_name: operatorName || '',
                operator_id: String(badge),
                machine_id: productionStore.machineId || 0,
                start_time: productionStart.toISOString(),
                end_time: eventTime,
                stop_reason: '', 
                DataSource: 'I',
                U_TipoDocumento: '1' // Produção
            };

            console.log("📤 [1/2] Fechando Produção (Manutenção):", productionPayload);
            await ProductionService.sendAppointment(productionPayload);
        }

        const stopPayload = {
            op_number: '',
            resource_code: machineRes,
            resource_name: machineName,                
            operator_name: operatorName || '',
            operator_id: String(badge),
            machine_id: productionStore.machineId || 0,
            DataSource: 'I',
            start_time: eventTime,
            end_time: eventTime, 
            stop_reason: currentPauseObj.value.reasonCode, 
            stop_description: 'Manutenção',
            U_TipoDocumento: '2'
        };

        console.log("📤 [2/2] Registrando Parada de Recurso:", stopPayload);
        await ProductionService.sendAppointment(stopPayload);

        await productionStore.sendEvent('STATUS_CHANGE', { 
            new_status: 'MAINTENANCE', 
            reason: 'Manutenção / Conserto' 
        });

        await productionStore.setMachineStatus('Em manutenção');
        await productionStore.finishSession();
        await productionStore.logoutOperator('MAINTENANCE'); 

        await router.push({ 
            name: 'machine-kiosk', 
            query: { 
                state: 'maintenance',
                last_operator: String(badge)
            } 
        });
        
        $q.notify({ type: 'warning', icon: 'build', message: 'Máquina em Manutenção.' });

    } catch (error) {
        console.error("Erro ao processar quebra de máquina:", error);
        $q.notify({ type: 'negative', message: 'Erro ao registrar parada no SAP.' });
    } finally {
        $q.loading.hide();
    }
}

async function finishPauseAndResume(fromPlc = false) {
  if (!currentPauseObj.value) return;
  
  if (!isPaused.value) {
      console.warn("⚠️ Tentativa de retomada duplicada ignorada.");
      return;
  }

  isPaused.value = false;
  if (activeOrder.value) activeOrder.value.status = 'RUNNING';
  
  if (productionStore.currentMachine) productionStore.currentMachine.status = 'Em uso';

  const isSetupReturn = currentPauseObj.value.reasonCode === '52';
  const msgLoading = isSetupReturn ? 'Finalizando Setup no SAP...' : 'Registrando Parada no SAP...';

  $q.loading.show({ message: msgLoading });
  
  try {
    const now = new Date();
    const pauseStart = new Date(currentPauseObj.value.startTime || statusStartTime.value); 
    const badge = productionStore.activeOperator?.badge || productionStore.currentOperatorBadge;

    const stopPayload = {
      op_number: '', 
      position: '',
      operation: '',
      stop_reason: String(currentPauseObj.value.reasonCode), 
      stop_description: currentPauseObj.value.reasonLabel,
      resource_code: productionStore.machineResource || '4.02.01',
      resource_name: productionStore.machineName || 'a a',
      operator_id: String(badge || '0'),
      operator_name: getOperatorName(String(badge || '')),
      machine_id: productionStore.machineId,
      start_time: pauseStart.toISOString(),
      end_time: now.toISOString(),
      DataSource: 'I',
      U_TipoDocumento: '2' 
    };

    await ProductionService.sendAppointment(stopPayload);


    if (!fromPlc || isSetupReturn) {
      console.log("🚀 Enviando status RUNNING (Fim de Pausa/Setup)");
      await productionStore.setMachineStatus('RUNNING');
      await productionStore.sendEvent('STATUS_CHANGE', { new_status: 'RUNNING' });
    } else {
      console.log("ℹ️ Retomada via PLC: Backend já atualizado.");
    }

    currentPauseObj.value = null; 
    statusStartTime.value = new Date(); 
    
    if (isSetupReturn) {
        $q.notify({ type: 'positive', message: 'Setup Finalizado! Produção iniciada.', icon: 'check_circle' });
    }

  } catch (error) {
    console.error("Erro ao retomar:", error);
    isPaused.value = true;
  } finally {
    $q.loading.hide();
  }
}
function confirmFinishOp() {
  let badge = productionStore.currentOperatorBadge;

  if (!badge && authStore.user?.employee_id) {
      const role = authStore.user.role || '';
      if (role !== 'admin' && role !== 'manager') badge = authStore.user.employee_id;
  }

  if (!badge || badge.includes('@')) {
      $q.dialog({
        title: 'Identificação Obrigatória',
        message: 'Bipe seu crachá para confirmar o encerramento:',
        prompt: { model: '', type: 'text', isValid: val => val.length > 0 },
        cancel: true, persistent: true
      }).onOk(data => {
        productionStore.currentOperatorBadge = data;
        confirmFinishOp(); 
      });
      return; 
  }

  $q.dialog({
    title: 'Encerrar Etapa / O.P.',
    message: 'Tem certeza que deseja finalizar esta etapa? A máquina ficará DISPONÍVEL.',
    cancel: true, persistent: true,
    ok: { label: 'SIM, ENCERRAR', color: 'negative', push: true, size: 'lg' }
  }).onOk(() => {
      void (async () => {
          $q.loading.show({ message: 'Encerrando sessão...' });
          
          try {
            if (inactivityTimer) clearTimeout(inactivityTimer);
            stopInactivityAlert();

            await productionStore.finishSession();

            await productionStore.setMachineStatus('AVAILABLE');
            
            await productionStore.logoutOperator('AVAILABLE', false, 'Etapa Finalizada pelo Operador');
            
            await router.push({ name: 'machine-kiosk' });

            $q.notify({ type: 'positive', message: 'Etapa concluída com sucesso!', icon: 'check_circle', timeout: 3000 });

          } catch (error) {
            console.error("Erro ao finalizar:", error);
            $q.notify({ type: 'negative', message: 'Erro ao comunicar com o servidor.' });
          } finally {
            $q.loading.hide();
            isStopDialogOpen.value = false;
          }
      })();
  });
}


function handleLogout() {
  $q.dialog({ title: 'Sair', message: 'Fazer logoff?', cancel: true }).onOk(() => {
    void (async () => {
        await productionStore.logoutOperator();
        await router.push({ name: 'machine-kiosk' });
    })();
  });
}

async function simulateOpScan() {
  $q.loading.show({
      message: 'Carregando melhor operação...',
      spinnerColor: 'teal-9',
      customClass: 'text-weight-bold text-h6'
  });
  await productionStore.requestOrderFromSAP('OP-TESTE-4500');
}
async function confirmAndonCall(sector: string) {
    isAndonDialogOpen.value = false;
    

    await productionStore.triggerAndon(sector, andonNote.value);
    
    andonNote.value = ''; 
    
    $q.notify({
        type: 'info',
        message: `Chamado enviado para: ${sector}`,
        icon: 'campaign'
    });
}




let scanBuffer = '';
let scanTimeout: ReturnType<typeof setTimeout> | null = null;

const onKeydown = (e: KeyboardEvent) => {
  void handleGlobalKeydown(e);
};

async function handleGlobalKeydown(event: KeyboardEvent) {
  if ((event.target as HTMLElement).tagName === 'INPUT') return;

  if (event.key === 'Enter') {
    if (scanBuffer.length > 2) {
      const scannedText = scanBuffer.trim();
      
      // 🚀 LÓGICA INTELIGENTE: Verifica se o operador já está logado
      const isOperatorLoggedIn = !!productionStore.currentOperatorBadge || !!authStore.user;

      // 1. SE JÁ ESTÁ LOGADO e aguardando OP -> O QR Code lido é uma O.P. ou O.S.
      if (isOperatorLoggedIn && !productionStore.activeOrder) {
          $q.loading.show({
              message: `Buscando Ordem ${scannedText} no SAP...`,
              spinnerColor: 'teal-9',
              customClass: 'text-weight-bold text-h6'
          });

          try {
              // Dispara a mesma rota que o clique da lista dispara!
              await productionStore.requestOrderFromSAP(scannedText);
          } catch (e) {
              console.error(e);
              $q.notify({ type: 'negative', message: 'Ordem não encontrada no SAP.' });
          } finally {
              scanBuffer = '';
              // Nota: O loading.hide() é chamado automaticamente pelo WebSocket quando a OP chega
          }
          return; // Sai da função para não tentar logar o crachá
      }

      // 2. CASO CONTRÁRIO -> O QR Code lido é um Crachá de Operador
      $q.loading.show({ message: `Autenticando crachá...` });
      
      try {
        await authStore.loginByBadge(scannedText);
        
        if (authStore.user?.employee_id) {
          productionStore.currentOperatorBadge = authStore.user.employee_id;
          $q.notify({ 
            type: 'positive', 
            message: `Olá, ${authStore.user.full_name}`,
            icon: 'person' 
          });

          if (!productionStore.activeOrder) {
             // Removido o openOpListDialog() para não forçar a lista na tela,
             // deixando o operador livre para escanear a OP agora.
          }
        } else {
          productionStore.currentOperatorBadge = scannedText;
        }
      } catch (e) {
        console.error("Erro ao ler crachá:", e);
        $q.notify({ type: 'negative', message: 'Crachá não reconhecido ou erro de conexão.' });
      } finally {
        $q.loading.hide();
        scanBuffer = '';
      }
    }
    scanBuffer = ''; 
  } else {
    if (event.key.length === 1) {
      scanBuffer += event.key;
      
      if (scanTimeout) clearTimeout(scanTimeout);
      scanTimeout = setTimeout(() => { scanBuffer = ''; }, 2000);
    }
  }
}

const stopDialogAlertActive = ref(false);
let inactivityTimer: ReturnType<typeof setTimeout> | null = null;
let beepInterval: ReturnType<typeof setInterval> | null = null;
let audioCtx: AudioContext | null = null;

function playBeep() {
  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    if (!audioCtx) audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
    const oscillator = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();
    
    oscillator.type = 'square';
    oscillator.frequency.setValueAtTime(800, audioCtx.currentTime);
    gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime); 
    
    oscillator.connect(gainNode);
    gainNode.connect(audioCtx.destination);
    
    oscillator.start();
    oscillator.stop(audioCtx.currentTime + 0.25);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  } catch (e) {
    console.warn("Áudio não suportado ou bloqueado pelo navegador.");
  }
}

function startInactivityAlert() {
  stopDialogAlertActive.value = true;
  playBeep(); 
  beepInterval = setInterval(playBeep, 1500); 
}

function stopInactivityAlert() {
  stopDialogAlertActive.value = false;
  if (beepInterval) clearInterval(beepInterval);
  beepInterval = null;
}

watch(isStopDialogOpen, (isOpen) => {
  if (isOpen) {
    const TRES_MINUTOS = 180000; 
    
    inactivityTimer = setTimeout(() => {
      startInactivityAlert();
    }, TRES_MINUTOS);
  } else {
    if (inactivityTimer) clearTimeout(inactivityTimer);
    stopInactivityAlert();
  }
});

onUnmounted(() => {
  if (inactivityTimer) clearTimeout(inactivityTimer);
  stopInactivityAlert();
  
  if (audioCtx && audioCtx.state !== 'closed') {
      audioCtx.close().catch(e => console.error(e));
  }
});

async function finishAutoSetup() {
    $q.loading.show({ message: 'Máquina ligada! Finalizando Setup...' });
    
    try {
        const now = new Date();
        const startSetup = statusStartTime.value; 
        // eslint-disable-next-line prefer-const
        let badge = productionStore.activeOperator.badge || productionStore.currentOperatorBadge;

        await ProductionService.sendAppointment({
            op_number: '', 
            resource_code: productionStore.machineResource,
            resource_name: productionStore.machineName, 
            operator_id: String(badge),
            operator_name: getOperatorName(String(badge || '')),
            start_time: startSetup.toISOString(),
            end_time: now.toISOString(),
            stop_reason: '52', 
            stop_description: 'Preparação / Setup',
            DataSource: 'I',
            U_TipoDocumento: '2'
        });

        productionStore.isInSetup = false; 
        statusStartTime.value = new Date();
        if (activeOrder.value) activeOrder.value.status = 'RUNNING';
        
        await productionStore.setMachineStatus('RUNNING');
        await productionStore.sendEvent('STATUS_CHANGE', { new_status: 'RUNNING' });

        $q.notify({ type: 'positive', message: 'Setup Finalizado. Produção Iniciada!', icon: 'rocket_launch' });

    } catch (error) {
        console.error("Erro na transição automática:", error);
    } finally {
        $q.loading.hide();
    }
}

const isProcessingSignal = ref(false);
let socket: WebSocket | null = null;

function connectWebSocket() {
  if (socket) {
      socket.close();
      socket = null;
  }

  const apiBase = import.meta.env.VITE_API_URL || 'http://192.168.0.22:8000/api/v1';
  const wsBase = apiBase.replace(/^http/, 'ws').replace('/api/v1', '');
  const wsUrl = `${wsBase}/ws/${productionStore.machineId}`;

  console.log(`🔌 Conectando ao WebSocket: ${wsUrl}`);
  socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    console.log("✅ WebSocket Conectado!");
    isSocketConnected.value = true;
  };

  socket.onmessage = async (event) => {
    try {
      const data = JSON.parse(event.data);

      if (data.machine_id && Number(data.machine_id) === Number(productionStore.machineId)) {
          if (data.new_status || data.machine_status_db) {
              if (productionStore.currentMachine) {
                  productionStore.currentMachine.status = data.machine_status_db || data.new_status;
              }
              setTimeout(() => {
                  void productionStore.fetchMachine(productionStore.machineId);
              }, 500);
          }
      }

      if (data.type === 'SAP_OPEN_ORDERS' && Number(data.machine_id) === Number(productionStore.machineId)) {
          console.log("📥 OPs recebidas via Celery!");
          openOps.value = data.data || [];
          loadingOps.value = false; 
          return; 
      }

      if (data.type === 'SAP_ORDER_DATA' && Number(data.machine_id) === Number(productionStore.machineId)) {
          $q.loading.hide(); 

          if (data.data) {
             console.log("📥 OP Encontrada via Celery:", data.code);
             await productionStore.processReceivedOrder(data.data);
             isStepConfirmationDialogOpen.value = true;
          } else {
             $q.notify({ type: 'negative', message: 'O.P. não encontrada no SAP' });
          }
          return;
      }

      // 🚀 INÍCIO DA NOVA LÓGICA DO DESENHO (CELERY)
      if (data.type === 'DRAWING_READY' && Number(data.machine_id) === Number(productionStore.machineId)) {
          console.log("🖼️ Desenho recebido do Celery!");
          if (isDrawingDialogOpen.value) {
              // O "?t=" quebra o cache do navegador
              drawingUrl.value = `${data.drawing_url}?t=${new Date().getTime()}`;
              
              // Injeta o Zoom na imagem
              nextTick(() => {
                  setTimeout(() => {
                      if (panzoomElement.value) {
                          if (panzoomInstance) panzoomInstance.destroy();
                          panzoomInstance = Panzoom(panzoomElement.value, {
                              maxScale: 10,
                              minScale: 1,
                              contain: 'outside',
                          });
                          const parent = panzoomElement.value.parentElement;
                          if (parent) {
                              parent.addEventListener('wheel', panzoomInstance.zoomWithWheel);
                          }
                      }
                  }, 100);
              });
          }
          return;
      }

      if (data.type === 'DRAWING_ERROR' && Number(data.machine_id) === Number(productionStore.machineId)) {
          console.error("❌ Erro no Celery ao buscar desenho:", data.message);
          if (isDrawingDialogOpen.value) {
              isDrawingDialogOpen.value = false; // Fecha a tela preta
              $q.notify({ type: 'negative', message: data.message || 'Erro ao carregar o desenho', icon: 'broken_image' });
          }
          return;
      }
      // 🚀 FIM DA NOVA LÓGICA DO DESENHO

      if (isShiftChangeDialogOpen.value) return;
      
      if (
        data.type === 'MACHINE_STATE_CHANGED' && 
        Number(data.machine_id) === Number(productionStore.machineId) &&
        !isProcessingSignal.value 
      ) {
        const rawStatus = String(data.new_status).toUpperCase();
        
        if (['1', 'RUNNING', 'PRODUCING', 'EM USO', 'IN_USE'].includes(rawStatus) && productionStore.isInSetup) {
             isProcessingSignal.value = true;
             await finishAutoSetup(); 
             isProcessingSignal.value = false;
             return;
        }

        if (data.category === 'UNPLANNED_STOP') {
          if (productionStore.isInSetup || isPaused.value) return;
          isProcessingSignal.value = true;
          await applyNormalPause(true); 
          isProcessingSignal.value = false;
        }
        
        else if (data.category === 'PRODUCING') {
          if (isPaused.value) {
            isProcessingSignal.value = true;
            isStopDialogOpen.value = false; 
            await finishPauseAndResume(true); 
            isProcessingSignal.value = false;
          }
        }
      }
    } catch (e) {
      console.error("Erro ao processar mensagem WebSocket:", e);
      isProcessingSignal.value = false;
    }
  };

  socket.onclose = () => {
    console.warn("⚠️ WebSocket Desconectado.");
    isSocketConnected.value = false;
    if (productionStore.activeOrder && !socket) {
        setTimeout(() => {
            if (productionStore.activeOrder) connectWebSocket();
        }, 5000); 
    }
  };

  socket.onerror = (error) => { console.error("❌ Erro no WebSocket:", error); };
}

onMounted(async () => {
  if (productionStore.currentStepIndex !== -1) {
    viewedStepIndex.value = productionStore.currentStepIndex;
  }

  timerInterval = setInterval(() => { 
    currentTime.value = new Date(); 
  }, 1000);
  resetTimer();

  window.addEventListener('keydown', onKeydown);
  window.addEventListener('online', updateOnlineStatus);
  window.addEventListener('offline', updateOnlineStatus);


  if (!productionStore.currentOperatorBadge && authStore.user?.employee_id) {
      productionStore.currentOperatorBadge = authStore.user.employee_id;
  }

  await syncOfflineData();

  if (productionStore.machineId) {
      await productionStore.fetchMachine(productionStore.machineId);
  }

  if (productionStore.activeOrder && (normalizedStatus.value === 'AUTÔNOMO' || normalizedStatus.value === 'OCIOSO')) {
      console.log("👤 Operador assumindo o posto (Troca Quente). Reivindicando máquina...");

      if (productionStore.currentMachine) {
          productionStore.currentMachine.status = 'Em uso'; 
          isPaused.value = false; 
      }

      await productionStore.setMachineStatus('RUNNING');
      
      await productionStore.sendEvent('STATUS_CHANGE', { 
          new_status: 'RUNNING', 
          reason: 'Operador assumiu máquina em movimento' 
      });

      resetTimer(); 
  }

  if (productionStore.machineId) {
      console.log("🔌 Iniciando conexão com Servidor (WebSocket)...");
      connectWebSocket();
  }
});

onUnmounted(() => {
    window.removeEventListener('keydown', onKeydown);
  window.removeEventListener('online', updateOnlineStatus);
  window.removeEventListener('offline', updateOnlineStatus);

  if (timerInterval) {
    clearInterval(timerInterval);
  }

  if (socket) {
    socket.close();
    socket = null;
    console.log("🔌 WebSocket desconectado (Componente desmontado).");
  }
});
</script>

<style>
.vemag-bg-primary { background-color: #008C7A !important; }
.vemag-text-primary { color: #008C7A !important; }
.vemag-bg-secondary { background-color: #66B8B0 !important; }
.vemag-text-secondary { color: #66B8B0 !important; }
.vemag-bg-light { background-color: #E0F2F1 !important; }
.bg-vemag-gradient { background: linear-gradient(135deg, #008C7A 0%, #00695C 100%); }
.bg-black-transparent { background-color: rgba(0,0,0,0.15); }
.hover-bg-grey-3:hover { background-color: #eeeeee; }
</style>

<style scoped>
.reason-card {
  border-radius: 12px;
  background: white;
  transition: all 0.3s ease;
  border: 1px solid #e0e0e0;
  min-height: 85px;
}

.reason-card:hover {
  background: #f5f5f5;
  transform: translateY(-2px);
  box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}


.special-active {
  border: 2px solid #008C7A !important; 
  background: #f0fdfa !important;
}

.pulse-animation {
  animation: pulse-shadow 2s infinite;
}
.critical-alert-flash {
  animation: flash-red-bg 1s infinite alternate !important;
}

@keyframes flash-red-bg {
  0% { 
    background-color: #ffebee !important; 
  }
  100% { 
    background-color: #ffcdd2 !important; 
    box-shadow: 0 0 50px rgba(211, 47, 47, 0.8) inset !important; 
  }
}

@keyframes pulse-shadow {
  0% { box-shadow: 0 0 0 0 rgba(0, 140, 122, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(0, 140, 122, 0); }
  100% { box-shadow: 0 0 0 0 rgba(0, 140, 122, 0); }
}

.lh-tight {
  line-height: 1.2;
}
.format-instructions {
  white-space: pre-wrap; 
  word-break: break-word; 
  line-height: 1.6; 
}
.font-inter { font-family: 'Roboto', sans-serif; }
.maintenance-dialog {
  width: 550px; 
  max-width: 95vw; 
  border-radius: 24px; 
  overflow: hidden;
  background: #ffffff;
}


.pulse-animation {
  animation: pulse-red 2s infinite;
  box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.7);
  border-radius: 50%;
}

@keyframes pulse-red {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 15px rgba(255, 255, 255, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 255, 255, 0); }
}

img, iframe {
  max-width: 100%;
}

.q-page {
  min-height: auto !important;
}

.q-btn--push.text-weight-bolder {
  border: 1px solid rgba(255, 255, 255, 0.3);
}
.maintenance-card {
  width: 600px;
  max-width: 95vw;
  border-radius: 20px;
}

.sub-reason-btn {
  border-radius: 12px;
  height: 80px;
  border: 1px solid #e0e0e0;
  color: #616161;
  background: #fafafa;
  transition: all 0.2s ease;
}

.sub-reason-active {
  background: #ffebee !important;
  border: 2px solid #b71c1c !important;
  color: #b71c1c !important;
  transform: scale(1.03);
}

.letter-spacing-1 {
  letter-spacing: 1px;
}
.font-monospace { font-family: 'Courier New', monospace; letter-spacing: -1px; }
.lh-small { line-height: 1.1; }
.col-grow { flex-grow: 1; }
.opacity-60 { opacity: 0.6; }
.opacity-50 { opacity: 0.5; }
.opacity-20 { opacity: 0.2; }
.opacity-80 { opacity: 0.8; }
.hover-scale-producing { transition: all 0.2s ease-in-out; }
.hover-scale-producing:active { transform: scale(0.98); }
.border-bottom-light { border-bottom: 2px solid #e0e0e0; }
.highlight-shift {
  border: 2px solid #ef6c00 !important; 
  background: #fff3e0 !important; 
  box-shadow: 0 4px 12px rgba(239, 108, 0, 0.2) !important;
}


.highlight-maintenance {
  border: 2px solid #b71c1c !important;
  background: #ffebee !important;
  box-shadow: 0 4px 12px rgba(183, 28, 28, 0.2) !important;
}

.highlight-setup {
  border: 2px solid #ca4bca !important;
  background: #fce5f8 !important; 
  box-shadow: 0 4px 12px rgba(213, 31, 219, 0.2) !important;
}


.pulse-animation {
  animation: pulse-ring 2s infinite;
}

@keyframes pulse-ring {
  0% { box-shadow: 0 0 0 0 rgba(0, 0, 0, 0.2); }
  70% { box-shadow: 0 0 0 10px rgba(0, 0, 0, 0); }
  100% { box-shadow: 0 0 0 0 rgba(0, 0, 0, 0); }
}

.reason-card {
  height: 90px;
  border-radius: 15px;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.reason-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 15px rgba(0,0,0,0.1);
}
</style>