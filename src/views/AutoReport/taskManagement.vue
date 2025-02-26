<template>
  <div class="task-management">
    <el-card class="box-card">
      <el-form :inline="true" :model="searchForm" class="demo-form-inline">
        <el-form-item label="游戏分类">
          <el-select v-model="searchForm.gameType" placeholder="请选择游戏分类">
            <el-option label="全部" value="" />
            <el-option label="游戏A" value="gameA" />
            <el-option label="游戏B" value="gameB" />
          </el-select>
        </el-form-item>
        <el-form-item label="任务名">
          <el-input v-model="searchForm.taskName" placeholder="请输入任务名" />
        </el-form-item>
        <el-form-item label="执行周期">
          <el-select v-model="searchForm.frequency" placeholder="请选择执行周期" @change="handleFrequencyChange">
            <el-option label="全部" value="" />
            <el-option label="日" value="day" />
            <el-option label="周" value="week" />
            <el-option label="月" value="month" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="searchForm.frequency === 'week'" label="每周">
          <el-select v-model="searchForm.dayOfWeek" placeholder="请选择每周">
            <el-option label="全部" value="" />
            <el-option label="周一" value="1" />
            <el-option label="周二" value="2" />
            <el-option label="周三" value="3" />
            <el-option label="周四" value="4" />
            <el-option label="周五" value="5" />
            <el-option label="周六" value="6" />
            <el-option label="周日" value="7" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="searchForm.frequency === 'month'" label="每月">
          <el-select v-model="searchForm.dayOfMonth" placeholder="请选择每月">
            <el-option label="全部" value="" />
            <el-option v-for="n in 31" :key="n" :label="n" :value="n" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="onSearch">查询</el-button>
        </el-form-item>
      </el-form>
      <el-table
        :data="tableData"
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="gameType" label="游戏分类" width="120" />
        <el-table-column prop="taskName" label="任务名" width="180" />
        <el-table-column label="执行周期" width="150">
          <template slot-scope="scope">
            <span>{{ formatFrequency(scope.row.frequency, scope.row.dayOfMonth, scope.row.dayOfWeek, scope.row.time) }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="last_run_at"
          label="最近执行时间"
          width="150"
          :formatter="formatDateTime"
        />
        <el-table-column prop="last_run_status" label="最近执行状态" width="120">
          <template slot-scope="scope">
            <el-tooltip v-if="scope.row.last_run_status === 'failure'" :content="scope.row.last_run_log" placement="top">
              <el-tag type="danger">Failure</el-tag>
            </el-tooltip>
            <el-tag v-else-if="scope.row.last_run_status === 'success'" type="success">Success</el-tag>
            <el-tag v-else type="info">未运行</el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="next_run_at"
          label="下次执行"
          width="150"
          :formatter="formatDateTime"
        />
        <el-table-column
          prop="created_at"
          label="创建时间"
          width="150"
          :formatter="formatDateTime"
        />
        <el-table-column
          prop="last_modified_at"
          label="最后修改"
          width="150"
          :formatter="formatDateTime"
        />
        <el-table-column label="操作" width="250">
          <template slot-scope="scope">
            <el-button size="mini" @click="handleViewSql(scope.row)">查看 SQL</el-button>
            <el-button size="mini" @click="handleEdit(scope.row)">编辑</el-button>
            <el-button size="mini" type="danger" @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="margin-top: 20px; display: flex; justify-content: space-between; align-items: center;">
        <el-button type="danger" :disabled="multipleSelection.length === 0" @click="handleBatchDelete">批量删除</el-button>
        <el-pagination
          :current-page="currentPage"
          :page-sizes="[20, 50, 100]"
          :page-size="pageSize"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
    <el-dialog
      title="SQL 信息"
      :visible.sync="dialogVisible"
      width="80%"
    >
      <el-table
        :data="sqlData"
        style="width: 100%"
      >
        <el-table-column
          prop="db_name"
          label="db_name"
          width="180"
        />
        <el-table-column
          prop="output_sql"
          label="output_sql"
          width="180"
        />
        <el-table-column
          prop="format"
          label="format"
          width="180"
        />
        <el-table-column
          prop="pos"
          label="pos"
          width="180"
        />
        <el-table-column
          prop="transpose"
          label="transpose(Y/N)"
          width="180"
        />
      </el-table>
      <span slot="footer" class="dialog-footer">
        <el-button @click="dialogVisible = false">确 定</el-button>
      </span>
    </el-dialog>
    <el-dialog
      title="编辑任务"
      :visible.sync="editDialogVisible"
      width="50%"
    >
      <el-alert
        title="如果要修改具体sql代码，请重新新建任务，本页仅支持运行周期相关修改。"
        type="warning"
        icon="el-icon-warning"
        :closable="false"
        style="margin-bottom: 30px;"
      />
      <el-form :model="editForm" label-width="120px">
        <el-form-item label="游戏分类">
          <el-select v-model="editForm.gameType" placeholder="请选择游戏分类">
            <el-option label="全部" value="" />
            <el-option label="游戏A" value="gameA" />
            <el-option label="游戏B" value="gameB" />
          </el-select>
        </el-form-item>
        <el-form-item label="任务名" style="margin-right: 50px;">
          <el-input v-model="editForm.taskName" placeholder="请输入任务名" />
        </el-form-item>
        <el-row>
          <el-col :span="24">
            <el-form-item label="执行周期">
              <el-select v-model="editForm.frequency" placeholder="请选择执行周期" @change="handleEditFrequencyChange">
                <el-option label="全部" value="" />
                <el-option label="日" value="day" />
                <el-option label="周" value="week" />
                <el-option label="月" value="month" />
              </el-select>
              <el-select v-if="editForm.frequency === 'week'" v-model="editForm.dayOfWeek" placeholder="请选择每周" style="margin-left: 10px;">
                <el-option label="全部" value="" />
                <el-option label="周一" value="1" />
                <el-option label="周二" value="2" />
                <el-option label="周三" value="3" />
                <el-option label="周四" value="4" />
                <el-option label="周五" value="5" />
                <el-option label="周六" value="6" />
                <el-option label="周日" value="7" />
              </el-select>
              <el-select v-if="editForm.frequency === 'month'" v-model="editForm.dayOfMonth" placeholder="请选择每月" style="margin-left: 10px;">
                <el-option label="全部" value="" />
                <el-option v-for="n in 31" :key="n" :label="n" :value="n" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row>
          <el-col :span="12">
            <el-form-item label="执行时间">
              <el-time-picker
                v-model="editForm.time"
                placeholder="选择时间"
                format="HH:mm"
                value-format="HH:mm"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button type="primary" @click="handleUpdate">更 新</el-button>
        <el-button @click="handleCancel">取 消</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import moment from 'moment'
export default {
  name: 'TaskManagement',
  data() {
    return {
      searchForm: {
        gameType: '',
        taskName: '',
        frequency: '',
        dayOfWeek: '',
        dayOfMonth: ''
      },
      tableData: [
        {
          gameType: '游戏A',
          taskName: '任务A',
          frequency: 'day',
          dayOfMonth: '',
          dayOfWeek: '',
          time: '10:00',
          last_run_at: '2025-02-26 10:00:00',
          last_run_status: 'success',
          last_run_log: '',
          next_run_at: '2025-02-27 10:00:00',
          created_at: '2025-02-25 10:00:00',
          last_modified_at: '2025-02-26 10:00:00'
        },
        {
          gameType: '游戏B',
          taskName: '任务B',
          frequency: 'week',
          dayOfMonth: '',
          dayOfWeek: '2',
          time: '11:00',
          last_run_at: '2025-02-25 11:00:00',
          last_run_status: 'failure',
          last_run_log: 'SQL 执行失败',
          next_run_at: '2025-03-04 11:00:00',
          created_at: '2025-02-24 11:00:00',
          last_modified_at: '2025-02-26 11:00:00'
        },
        {
          gameType: '游戏C',
          taskName: '任务C',
          frequency: 'month',
          dayOfMonth: '15',
          dayOfWeek: '',
          time: '12:00',
          last_run_at: null,
          last_run_status: null,
          last_run_log: null,
          next_run_at: '2025-03-15 12:00:00',
          created_at: '2025-02-23 12:00:00',
          last_modified_at: '2025-02-26 12:00:00'
        }
      ],
      multipleSelection: [],
      total: 100,
      currentPage: 1,
      pageSize: 20,
      dialogVisible: false,
      sqlData: [],
      editDialogVisible: false,
      editForm: {
        gameType: '',
        taskName: '',
        frequency: '',
        time: '',
        dayOfWeek: '',
        dayOfMonth: ''
      }
    }
  },
  methods: {
    handleSizeChange(size) {
      this.pageSize = size
      console.log(`每页 ${size} 条`)
    },
    handleCurrentChange(page) {
      this.currentPage = page
      console.log(`当前页: ${page}`)
    },
    handleFrequencyChange(value) {
      this.searchForm.dayOfWeek = ''
      this.searchForm.dayOfMonth = ''
    },
    handleEditFrequencyChange(value) {
      this.editForm.dayOfWeek = ''
      this.editForm.dayOfMonth = ''
    },
    formatFrequency(frequency, dayOfMonth, dayOfWeek, time) {
      if (frequency === 'day') {
        return `每日 ${time}`
      } else if (frequency === 'week') {
        let dayOfWeekStr = ''
        switch (String(dayOfWeek)) {
          case '1':
            dayOfWeekStr = '一'
            break
          case '2':
            dayOfWeekStr = '二'
            break
          case '3':
            dayOfWeekStr = '三'
            break
          case '4':
            dayOfWeekStr = '四'
            break
          case '5':
            dayOfWeekStr = '五'
            break
          case '6':
            dayOfWeekStr = '六'
            break
          case '7':
            dayOfWeekStr = '日'
            break
        }
        return `每周${dayOfWeekStr} ${time}`
      } else if (frequency === 'month') {
        return `每月${dayOfMonth} 号 ${time}`
      } else {
        return ''
      }
    },
    formatDateTime(row, column) {
      const date = row[column.property]
      if (date) {
        return moment(date).format('YYYY-MM-DD HH:mm')
      } else {
        return ''
      }
    },
    handleViewSql(row) {
      this.dialogVisible = true
      this.sqlData = [
        {
          db_name: '数据库A',
          output_sql: 'SELECT * FROM tableA',
          format: 'CSV',
          pos: '1',
          transpose: 'Y'
        }
      ]
    },
    handleEdit(row) {
      this.editDialogVisible = true
      this.editForm = {
        gameType: row.gameType,
        taskName: row.taskName,
        frequency: row.frequency,
        time: row.time,
        dayOfWeek: row.dayOfWeek,
        dayOfMonth: row.dayOfMonth
      }
    },
    handleUpdate() {
      console.log('update', this.editForm)
      this.editDialogVisible = false
    },
    handleCancel() {
      this.editDialogVisible = false
    },
    handleSelectionChange(val) {
      this.multipleSelection = val
    },
    handleDelete(row) {
      console.log('delete', row)
    },
    handleBatchDelete() {
      console.log('batch delete', this.multipleSelection)
    }
  }
}
</script>
